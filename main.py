import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtGui import *

class HistoryDialog(QDialog):
    def __init__(self, parent):
        super(HistoryDialog, self).__init__(parent)
        self.browser = parent
        self.setWindowTitle("Browsing History")
        self.layout = QVBoxLayout()
        self.history_list = QListWidget()
        self.layout.addWidget(self.history_list)
        self.button_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected)
        self.button_layout.addWidget(self.delete_button)

        self.delete_all_button = QPushButton("Delete All")
        self.delete_all_button.clicked.connect(self.delete_all)
        self.button_layout.addWidget(self.delete_all_button)
        
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)
        self.load_history()

    def load_history(self):
        with open('history.txt', 'r') as file:
            for line in file:
                item = QListWidgetItem(line.strip())
                self.history_list.addItem(item)
        self.history_list.itemClicked.connect(self.navigate_to_url)

    def navigate_to_url(self, item):
        url = item.text()
        self.browser.navigate_to_url(url)
        self.close()

    def delete_selected(self):
        selected_items = self.history_list.selectedItems()
        for item in selected_items:
            self.history_list.takeItem(self.history_list.row(item))
        with open('history.txt', 'w') as file:
            for index in range(self.history_list.count()):
                file.write(self.history_list.item(index).text() + '\n')
                
    def delete_all(self):
        self.history_list.clear()
        with open('history.txt', 'w') as file:
            pass

class BrowserTab(QWebEngineView):
    def __init__(self, tabs, browser, update_url_func, add_to_history_func):
        super(BrowserTab, self).__init__()
        self.tabs = tabs
        self.browser = browser
        self.setUrl(QUrl('https://search.louiml.net'))
        self.titleChanged.connect(self.update_tab_title)
        self.iconChanged.connect(self.update_tab_icon)
        self.urlChanged.connect(update_url_func)
        self.urlChanged.connect(add_to_history_func)
        self.loadFinished.connect(self.on_load_finished)

    def update_tab_title(self, title):
        current_index = self.tabs.currentIndex()
        self.tabs.setTabText(current_index, title)
        
    def update_tab_icon(self, icon):
        current_index = self.tabs.currentIndex()
        if icon.isNull():
            icon = QIcon('./public/no_icon_icon.png')
        self.tabs.setTabIcon(current_index, icon)
        
    def on_load_finished(self):
        current_url = self.url().toString()
        if current_url.endswith('.json'):
            self.add_json_highlighting()
            
    def createWindow(self, _type):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            new_tab = BrowserTab(self.tabs, self.browser, self.browser.update_url, self.browser.add_to_history)
            tab_index = self.tabs.addTab(new_tab, 'New Tab')
            self.tabs.setCurrentIndex(tab_index)
            return new_tab
        return QWebEngineView.createWindow(self, _type)
    
    def add_json_highlighting(self):
        def inject_prism_js(result=None):
            with open('./prismjs/prism.js', 'r') as f:
                prism_js = f.read()
            self.page().runJavaScript(prism_js, wrap_content)
        
        def wrap_content(result=None):
            wrap_js = """
            var content = document.body.innerText;
            document.body.innerHTML = '<pre><code class=\\"language-json\\">' + content + '</code></pre>';
            """
            self.page().runJavaScript(wrap_js, highlight_content)
        
        def highlight_content(result=None):
            highlight_js = "Prism.highlightAll();"
            self.page().runJavaScript(highlight_js)
        
        with open('./prismjs/prism.css', 'r') as f:
            prism_css = f.read()
        
        css_code = f"""
        var style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = `{prism_css}`;
        document.head.appendChild(style);
        """
        
        self.page().runJavaScript(css_code, inject_prism_js)

class Browser(QMainWindow):
    def __init__(self):
        super(Browser, self).__init__()
        
        self.setWindowTitle("Creag")

        app_icon = QIcon('./public/icon.ico')
        self.setWindowIcon(app_icon)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        self.showMaximized()

        initial_tab = BrowserTab(self.tabs, self, self.update_url, self.add_to_history)
        self.tabs.addTab(initial_tab, 'New Tab')
        
        self.tabs.currentChanged.connect(self.on_tab_changed)

        navbar = QToolBar()
        navbar.setIconSize(QSize(16, 16))
        self.addToolBar(navbar)

        navbar.setStyleSheet("""
            background-color: #2C3333;
            border: none;
            padding: 5px;
        """)

        back_icon = QIcon('./public/back_icon.png')
        forward_icon = QIcon('./public/forward_icon.png')
        reload_icon = QIcon('./public/reload_icon.png')
        home_icon = QIcon('./public/home_icon.png')
        new_tab_icon = QIcon('./public/new_tab_icon.png')

        back_btn = QAction(back_icon, 'Back', self)
        back_btn.triggered.connect(self.tabs.currentWidget().back)
        navbar.addAction(back_btn)

        forward_btn = QAction(forward_icon, 'Forward', self)
        forward_btn.triggered.connect(self.tabs.currentWidget().forward)
        navbar.addAction(forward_btn)

        reload_btn = QAction(reload_icon, 'Reload', self)
        reload_btn.triggered.connect(self.reload_page)
        navbar.addAction(reload_btn)

        home_btn = QAction(home_icon, 'Home', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        new_tab_btn = QAction(new_tab_icon, 'New Tab', self)
        new_tab_btn.triggered.connect(self.create_new_tab)
        navbar.addAction(new_tab_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setStyleSheet("""
            border: 2px solid #ccc;
            border-radius: 5px;
            padding: 2px;
            background: #040D12;
            padding-left: 10px;
            color: white;
        """)
        navbar.addWidget(self.url_bar)
        
        history_icon = QIcon('./public/history_icon.png')
        history_btn = QAction(history_icon, 'History', self)
        history_btn.triggered.connect(self.show_history)
        navbar.addAction(history_btn)

        self.tabs.currentWidget().urlChanged.connect(self.update_url)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl('https://search.louiml.net'))
        
    def reload_page(self):
        self.tabs.currentWidget().reload()
        
    def add_to_history(self, q):
        url = q.toString()
        with open('history.txt', 'a') as file:
            file.write(url + '\n')

    def show_history(self):
        self.history_dialog = HistoryDialog(self)
        self.history_dialog.exec_()
        
    def create_new_tab(self):
        new_tab = BrowserTab(self.tabs, self, self.update_url, self.add_to_history)
        tab_index = self.tabs.addTab(new_tab, 'New Tab')
        self.tabs.setCurrentIndex(tab_index)
        
    def show_cookies(self):
        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        cookie_store.cookieAdded.connect(self.print_cookie)

    def print_cookie(self, cookie):
        print("Cookie added:")
        print("Name:", cookie.name().data().decode("utf-8"))
        print("Value:", cookie.value().data().decode("utf-8"))
        print("Domain:", cookie.domain().encode("utf-8"))
        print("Path:", cookie.path().encode("utf-8"))

    def navigate_to_url(self, url=None):
        if url is None:
            url = self.url_bar.text()
        if '.' not in url:
            url = 'https://duckduckgo.com/?q=' + url
        elif 'http' not in url:
            url = 'https://' + url
        self.tabs.currentWidget().setUrl(QUrl(url))
        with open('history.txt', 'a') as file:
            file.write(url + '\n')

    def update_url(self, q):
        self.url_bar.setText(q.toString())

    def on_tab_changed(self, index):
        current_url = self.tabs.currentWidget().url().toString()
        self.url_bar.setText(current_url)

    def createWindow(self, _type):
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            new_tab = BrowserTab(self.browser, self.tabs, self.browser.update_url, self.browser.add_to_history)
            tab_index = self.tabs.addTab(new_tab, 'New Tab')
            self.tabs.setCurrentIndex(tab_index)
            return new_tab
        return QWebEngineView.createWindow(self, _type)

    def close_tab(self, index):
        self.tabs.removeTab(index)

app = QApplication(sys.argv)
QApplication.setApplicationName('Browser')
window = Browser()
app.exec_()
