import sys
import os
import re
import subprocess
import platform
from urllib.parse import urlparse
      
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-low-res-tiling --no-first-run"

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QMainWindow, QFrame,
    QTabWidget, QToolButton
)

from PySide6.QtGui import QIcon

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo
)

# ----------------------------- POLICY ---------------------------------

class PolicyDecision:
    def __init__(self, action, confidence, reason):
        self.action = action
        self.confidence = confidence
        self.reason = reason


class PolicyEngine:

    def __init__(self):

        self.blocked_domains = {
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "googletagmanager.com",
            "adservice.google.com",
            "pagead2.googlesyndication.com",
            "tpc.googlesyndication.com",
            "ad.doubleclick.net",
            "g.doubleclick.net",
            "ads.google.com",
            "2mdn.net",
            "facebook.com/tr",
            "connect.facebook.net"
        }

        self.telemetry_domains = {
            "youtube.com",
            "google.com",
            "googlevideo.com",
            "ytimg.com"
        }

        self.patterns = [
            re.compile(r"/ptracking"),
            re.compile(r"/log_event"),
            re.compile(r"/tracking"),
            re.compile(r"/pixel"),
            re.compile(r"/analytics")
        ]

    def match(self, host, domain):
        return host == domain or host.endswith("." + domain)

    def evaluate(self, url, resource_type):

        parsed = urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path.lower()

        for d in self.blocked_domains:
            if self.match(host, d):
                return PolicyDecision("BLOCK", 1.0, "blocked domain")

        if any(self.match(host, d) for d in self.telemetry_domains):

            if resource_type in (
                QWebEngineUrlRequestInfo.ResourceType.Xhr,
                QWebEngineUrlRequestInfo.ResourceType.Script,
                QWebEngineUrlRequestInfo.ResourceType.Fetch
            ):

                for p in self.patterns:
                    if p.search(path):
                        return PolicyDecision("BLOCK", 0.9, "telemetry")

        return PolicyDecision("ALLOW", 1.0, "clean")


class RequestInterceptor(QWebEngineUrlRequestInterceptor):

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        decision = self.engine.evaluate(url, info.resourceType())

        if decision.action == "BLOCK":
            info.block(True)

# ----------------------------- DASHBOARD ---------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
body {
    background:#0f0f0f;
    color:white;
    font-family:sans-serif;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    height:100vh;
    margin:0;
}
.grid {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:20px;
}
.tile {
    width:120px;
    height:120px;
    background:#1a1a1a;
    border-radius:12px;
    display:flex;
    align-items:center;
    justify-content:center;
    text-decoration:none;
    color:white;
}
</style>
</head>
<body>
<h1>Eleuther</h1>
<div class="grid">
<a class="tile" href="https://www.youtube.com">YouTube</a>
<a class="tile" href="https://www.twitch.tv">Twitch</a>
<a class="tile" href="https://github.com">GitHub</a>
<a class="tile" href="https://www.reddit.com">Reddit</a>
</div>
</body>
</html>
"""

# ----------------------------- CONTEXT ---------------------------------

class BrowserContext:

    def __init__(self, name="Eleuther_Profile", incognito=False):

        if incognito:
            self.profile = QWebEngineProfile()
        else:
            self.profile = QWebEngineProfile(name)

            base = os.path.dirname(os.path.abspath(__file__))
            self.profile.setCachePath(os.path.join(base, "cache"))
            self.profile.setPersistentStoragePath(os.path.join(base, "storage"))

        self.engine = PolicyEngine()
        self.interceptor = RequestInterceptor(self.engine)
        self.profile.setUrlRequestInterceptor(self.interceptor)

# ----------------------------- PAGE ---------------------------------

class Page(QWebEnginePage):
    def acceptNavigationRequest(self, url, nav_type, main_frame):
        return True

# ----------------------------- TAB ---------------------------------

class Tab(QWidget):

    def __init__(self, profile, dashboard=True):

        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = QWebEngineView()
        self.view.setPage(Page(profile, self.view))

        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

        layout.addWidget(self.view)

        if dashboard:
            self.view.setHtml(DASHBOARD_HTML)
        else:
            self.view.setUrl(QUrl("https://www.google.com"))

# ----------------------------- MAIN ---------------------------------

class MainWindow(QMainWindow):

    def __init__(self, ctx):

        super().__init__()

        self.ctx = ctx

        self.setWindowTitle("Eleuther Browser")
        self.resize(1400, 900)

        root = QWidget()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)

        # ---------------- TOOLBAR ----------------
        bar = QFrame()
        bar_layout = QHBoxLayout(bar)

        self.back = QPushButton("←")
        self.forward = QPushButton("→")
        self.reload = QPushButton("⟳")

        self.url = QLineEdit()
        self.url.setPlaceholderText("Search or enter URL...")

        self.go = QPushButton("Go")

        self.incognito = QToolButton()
        self.incognito.setText("Incognito")

        bar_layout.addWidget(self.back)
        bar_layout.addWidget(self.forward)
        bar_layout.addWidget(self.reload)
        bar_layout.addWidget(self.url)
        bar_layout.addWidget(self.go)
        bar_layout.addWidget(self.incognito)

        main.addWidget(bar)

        # ---------------- TABS ----------------
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)

        main.addWidget(self.tabs)

        self.add_tab(True)

        # wiring (minimal but functional)
        self.go.clicked.connect(self.navigate)

        self.back.clicked.connect(lambda: self.current().view.back())
        self.forward.clicked.connect(lambda: self.current().view.forward())
        self.reload.clicked.connect(lambda: self.current().view.reload())

    def current(self):
        return self.tabs.currentWidget()

    def add_tab(self, dashboard=True):

        tab = Tab(self.ctx.profile, dashboard)
        i = self.tabs.addTab(tab, "Tab")
        self.tabs.setCurrentIndex(i)

    def navigate(self):

        text = self.url.text().strip()
        if not text:
            return

        qurl = QUrl.fromUserInput(text)

        self.current().view.setUrl(qurl)

# ----------------------------- RUN ---------------------------------

def main():

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    ctx = BrowserContext()
    win = MainWindow(ctx)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
