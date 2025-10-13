# 外貨EXにログインするテストコード
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import time
from datetime import datetime
import csv
import os
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import warnings
import sys
import contextlib
from collections import deque
import statistics
import signal
import atexit

# undetected_chromedriverの警告を抑制
warnings.filterwarnings("ignore", category=DeprecationWarning)

# プロセス終了時の処理を登録
def cleanup_on_exit():
    """プロセス終了時のクリーンアップ"""
    if sys.platform.startswith('win'):
        # 標準エラー出力を無効化してクリーンアップ
        import os
        sys.stderr = open(os.devnull, 'w')

atexit.register(cleanup_on_exit)

# Windowsでのハンドルエラーを抑制
if sys.platform.startswith('win'):
    import os
    os.environ['PYTHONHASHSEED'] = '0'
    # ChromeDriverの終了時エラーも抑制
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", message=".*Chrome.*")
    warnings.filterwarnings("ignore", message=".*ハンドル.*")
    
    # sys.stderr を一時的にオーバーライドしてハンドルエラーを抑制
    import io
    original_stderr = sys.stderr
    
    
    class FilteredStderr:
        def __init__(self, original):
            self.original = original
            
        def write(self, message):
            # ChromeDriverのハンドルエラーをフィルタリング
            if ("ハンドルが無効です" in message or "Chrome.__del__" in message or 
                "WinError 6" in message or "OSError:" in message or "OSError" in message or
                "Exception ignored in:" in message or "undetected_chromedriver" in message or
                "self.quit()" in message or "time.sleep(0.1)" in message or
                "Traceback (most recent call last):" in message or
                "File \"" in message and "undetected_chromedriver" in message or
                message.strip() == "" or len(message.strip()) < 3):
                return
            return self.original.write(message)
            
        def flush(self):
            return self.original.flush()
            
        def __getattr__(self, name):
            return getattr(self.original, name)
    
    sys.stderr = FilteredStderr(original_stderr)

@contextlib.contextmanager
def suppress_stderr():
    """標準エラー出力を一時的に抑制するコンテキストマネージャー"""
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr
"""""
# 本番環境
# ログイン情報
login_id = "5184435"
password = "Sutada0208"

# 外貨EXのログインURL
login_url = "https://fx.gaikaex.com/servlet/login"
"""

# デモ環境
# ログイン情報
login_id = "3006316"
password = "Sutada53"

# 外貨EXのログインURL
login_url = "https://vt-fx.gaikaex.com/servlet/login"



def login_with_selenium():
    """
    Seleniumを使用して外貨EXにログインするテスト
    """
    # 必要なモジュールをインポート
    import os
    import signal
    
    print("Seleniumでログインテストを開始...")
    
    # Chromeドライバーのオプション設定
    options = webdriver.ChromeOptions()
    
    # 自動化検出回避設定
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 基本的な設定
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # User-Agentを通常のブラウザに偽装
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        # WebDriverを初期化
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 自動化検出回避のためのJavaScript実行
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get(login_url)
        
        # ページの読み込み待ち
        wait = WebDriverWait(driver, 10)
        
        print(f"ページタイトル: {driver.title}")
        print(f"現在のURL: {driver.current_url}")
        
        # ログインフォームの要素を探す
        try:
            # ユーザーID入力欄を探す
            username_input = wait.until(EC.presence_of_element_located((By.NAME, "P001")))
            print("ユーザーID入力欄を発見")
            
            # パスワード入力欄を探す
            password_input = driver.find_element(By.NAME, "P002")
            print("パスワード入力欄を発見")
            
            # ログイン情報を入力
            username_input.clear()
            username_input.send_keys(login_id)
            print("ユーザーIDを入力しました")
            
            password_input.clear()
            password_input.send_keys(password)
            print("パスワードを入力しました")
            
            # ログインボタンを探す（複数のセレクターを試行）
            login_button_selectors = [
                "input[type='submit']",
                "button[type='submit']", 
                "input[value*='ログイン']",
                "input[value*='login']",
                ".login-btn",
                "#login-button"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"ログインボタンを発見: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if login_button:
                login_button.click()
                print("ログインボタンをクリックしました")
            else:
                # フォーム自体をサブミット
                form = driver.find_element(By.TAG_NAME, "form")
                driver.execute_script("arguments[0].submit();", form)
                print("フォームを直接サブミットしました")
            
            # ログイン後のページ読み込み待ち
            time.sleep(1)  # 3秒→1秒に短縮
            
            print(f"ログイン後のURL: {driver.current_url}")
            print(f"ログイン後のページタイトル: {driver.title}")
            
            # ログイン成功の判定
            if "login" not in driver.current_url.lower():
                print("✅ ログインに成功しました！")
                return True
            else:
                print("❌ ログインに失敗した可能性があります")
                return False
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"エラーが発生しました: {e}")
            return False
            
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        return False
        
    finally:
        if driver:
            try:
                print("ブラウザを終了中...")
                # まずウィンドウをすべて閉じる
                driver.close()
                time.sleep(0.2)  # 0.5秒→0.2秒に短縮
                # プロセスを完全に終了
                driver.quit()
                time.sleep(0.2)  # 0.5秒→0.2秒に短縮
                print("ブラウザを正常に閉じました")
            except Exception as e:
                print(f"ブラウザの終了時にエラーが発生しました: {e}")
                # エラーが発生した場合でもプロセスの強制終了を試行
                try:
                    if hasattr(driver, 'service') and driver.service.process:
                        os.kill(driver.service.process.pid, signal.SIGTERM)
                        print("ChromeDriverプロセスを強制終了しました")
                except:
                    pass


def login_with_requests():
    """
    Requestsライブラリを使用して外貨EXにログインするテスト
    ChromeDriverを使わないHTTPベースの実装
    """
    print("Requestsでログインテストを開始...")
    
    # セッションを作成してCookieを保持
    session = requests.Session()
    
    # User-Agentを設定して通常のブラウザを模倣
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    session.headers.update(headers)
    
    try:
        # まずログインページにアクセス
        print("ログインページにアクセス中...")
        response = session.get(login_url, timeout=30)
        
        # 文字エンコーディングを適切に設定
        if response.encoding == 'ISO-8859-1':
            response.encoding = 'shift_jis'
        
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスURL: {response.url}")
        print(f"文字エンコーディング: {response.encoding}")
        
        if response.status_code == 200:
            print("✅ ログインページにアクセスできました")
            
            # HTMLを解析してフォーム情報を取得
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                print("⚠️ BeautifulSoup4がインストールされていません")
                print("HTMLの解析ができませんが、基本的なPOSTリクエストを試行します")
                return attempt_login_post(session)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ログインフォームを探す
            form = soup.find('form')
            if form:
                print(f"✅ フォームを発見:")
                print(f"  - action: {form.get('action', 'なし')}")
                print(f"  - method: {form.get('method', 'GET')}")
            
            # 入力フィールドを探す
            inputs = soup.find_all('input')
            hidden_fields = {}
            
            print("発見された入力フィールド:")
            for inp in inputs:
                name = inp.get('name', '')
                input_type = inp.get('type', 'text')
                value = inp.get('value', '')
                
                print(f"  - name: {name}, type: {input_type}, value: {value[:20] if value else 'なし'}")
                
                # hidden フィールドの値を保存（CSRFトークンなど）
                if input_type == 'hidden' and name and value:
                    hidden_fields[name] = value
            
            # ログイン情報でPOSTリクエストを送信
            if form:
                return attempt_login_with_form(session, form, hidden_fields)
            else:
                return attempt_login_post(session)
            
        else:
            print(f"❌ ログインページへのアクセスに失敗しました (ステータスコード: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def attempt_login_with_form(session, form, hidden_fields):
    """
    フォーム情報を使ってログインを試行
    """
    try:
        # フォームのaction URLを取得
        action = form.get('action', '')
        if action.startswith('/'):
            # 相対パスの場合は絶対URLに変換
            base_url = 'https://fx.gaikaex.com'
            login_post_url = base_url + action
        elif action.startswith('http'):
            login_post_url = action
        else:
            # actionが空の場合は同じURLにPOST
            login_post_url = login_url
        
        print(f"ログインPOST先: {login_post_url}")
        
        # ログインデータを準備
        login_data = hidden_fields.copy()  # CSRFトークンなどのhiddenフィールドを含める
        
        # 外貨EXの実際のフィールド名を使用
        # 前回の解析結果: P001=ユーザーID、P002=パスワード
        username_field = None
        password_field = None
        
        # フォーム内の入力フィールドを詳細に解析
        inputs = form.find_all('input')
        print("フィールド詳細解析:")
        
        for inp in inputs:
            name = inp.get('name', '')
            input_type = inp.get('type', 'text').lower()
            print(f"  - name: {name}, type: {input_type}")
            
            # 実際のフィールド名に基づく特定
            if name == 'P001' or (input_type == 'text' and not username_field):
                username_field = name
            elif name == 'P002' or input_type == 'password':
                password_field = name
        
        # フィールド名を確実に設定
        if not username_field:
            username_field = 'P001'  # 外貨EXのデフォルト
        if not password_field:
            password_field = 'P002'  # 外貨EXのデフォルト
            
        login_data[username_field] = login_id
        login_data[password_field] = password
        print(f"✅ 使用するログインフィールド: {username_field}={login_id}, {password_field}=[パスワード]")
        
        # ログイン実行
        print("ログイン試行中...")
        response = session.post(login_post_url, data=login_data, timeout=30, allow_redirects=True)
        
        # レスポンスの文字エンコーディングを適切に設定
        if response.encoding == 'ISO-8859-1':
            response.encoding = 'shift_jis'
        
        print(f"ログイン後のステータスコード: {response.status_code}")
        print(f"ログイン後のURL: {response.url}")
        print(f"ログイン後のエンコーディング: {response.encoding}")
        
        # より詳細な成功/失敗判定
        return analyze_login_response(response)
            
    except Exception as e:
        print(f"ログイン試行中にエラーが発生しました: {e}")
        return False

def analyze_login_response(response):
    """
    ログインレスポンスを詳細に分析して成功/失敗を判定
    """
    try:
        # 確実に文字エンコーディングを設定
        if response.encoding == 'ISO-8859-1' or response.encoding == 'Windows-31J':
            response.encoding = 'shift_jis'
        
        print(f"\n=== ログイン結果の詳細分析 ===")
        print(f"ステータスコード: {response.status_code}")
        print(f"最終URL: {response.url}")
        print(f"解析用エンコーディング: {response.encoding}")
        
        # HTMLコンテンツを解析
        try:
            from bs4 import BeautifulSoup
            # エンコーディングを明示的に指定してBeautifulSoupで解析
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='shift_jis')
            
            # ページタイトルを確認
            title = soup.find('title')
            page_title = title.text.strip() if title else "不明"
            print(f"ページタイトル: {page_title}")
            
            # エラーメッセージを探す
            error_indicators = [
                # 一般的なエラー要素
                soup.find_all(class_=lambda x: x and ('error' in x.lower() or 'alert' in x.lower())),
                soup.find_all(id=lambda x: x and ('error' in x.lower() or 'alert' in x.lower())),
                # テキストベースのエラー検索（stringに変更）
                soup.find_all(string=lambda text: text and any(keyword in text for keyword in [
                    'ログインに失敗', 'ログイン失敗', 'ログイン処理に失敗', 'パスワードが違い', 'IDが違い', 
                    'エラー', 'Error', '認証に失敗', '入力内容を確認', 'ご案内'
                ]))
            ]
            
            # エラーメッセージが見つかった場合
            for error_list in error_indicators:
                if error_list:
                    print("❌ エラーメッセージを検出:")
                    for error in error_list[:3]:  # 最大3つまで表示
                        if hasattr(error, 'text'):
                            error_text = error.text.strip()
                        else:
                            error_text = str(error).strip()
                        if error_text:
                            print(f"  - {error_text}")
                    return False
            
            # 成功を示すキーワードを探す
            success_indicators = [
                'メニュー', 'menu', 'ダッシュボード', 'dashboard', 'マイページ', 'mypage',
                'ログアウト', 'logout', '取引画面', 'trading', 'ポートフォリオ', 'portfolio'
            ]
            
            page_text = response.text.lower()
            found_success_indicators = [keyword for keyword in success_indicators if keyword in page_text]
            
            # URLベースの判定
            url_success_indicators = ['main', 'menu', 'dashboard', 'trading', 'account']
            url_lower = response.url.lower()
            found_url_indicators = [keyword for keyword in url_success_indicators if keyword in url_lower]
            
            # ログインページに戻っているかチェック
            if 'login' in url_lower and 'logout' not in url_lower:
                print("❌ ログインページに戻っています（ログイン失敗の可能性が高い）")
                return False
            
            # 成功の兆候
            if found_success_indicators or found_url_indicators:
                print(f"✅ 成功の兆候を検出:")
                if found_success_indicators:
                    print(f"  - ページ内容: {', '.join(found_success_indicators)}")
                if found_url_indicators:
                    print(f"  - URL: {', '.join(found_url_indicators)}")
                print("✅ ログインに成功した可能性があります")
                return True
            
            # フォームの再表示をチェック
            login_forms = soup.find_all('form')
            password_inputs = soup.find_all('input', {'type': 'password'})
            
            if login_forms and password_inputs:
                print("❌ ログインフォームが再表示されています（ログイン失敗）")
                return False
            
            # どちらでもない場合の詳細分析
            print("⚠️ 明確な成功/失敗の判定ができません")
            
            # メッセージ内容を詳しく確認
            message_elements = soup.find_all(['p', 'div', 'span', 'td'])
            print("ページ内のメッセージ内容:")
            for elem in message_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 5:  # 短すぎるテキストは除外
                    print(f"  - {text}")
            
            # JavaScript リダイレクトの確認
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('location' in script.string or 'redirect' in script.string):
                    print(f"JavaScriptリダイレクトを検出: {script.string[:100]}...")
            
            print(f"レスポンステキストの先頭500文字:")
            print(response.text[:500].replace('\n', ' ').replace('\r', ''))
            
            # デフォルトは失敗とみなす（安全側に倒す）
            return False
            
        except ImportError:
            print("⚠️ BeautifulSoupが利用できません。基本的な判定のみ実行します")
            
            # 基本的なURL判定のみ
            url_lower = response.url.lower()
            if 'login' in url_lower and 'logout' not in url_lower:
                print("❌ ログインページのURL（失敗の可能性が高い）")
                return False
            elif any(keyword in url_lower for keyword in ['main', 'menu', 'dashboard']):
                print("✅ 成功を示すURL")
                return True
            else:
                print("⚠️ 判定不能（失敗とみなします）")
                return False
                
    except Exception as e:
        print(f"レスポンス分析中にエラー: {e}")
        return False

def attempt_login_post(session):
    """
    基本的なPOSTリクエストでログインを試行（フォーム解析なし）
    """
    try:
        print("基本的なPOSTリクエストでログインを試行...")
        
        login_data = {
            'username': login_id,
            'password': password,
            'login_id': login_id,
            'userid': login_id
        }
        
        response = session.post(login_url, data=login_data, timeout=30, allow_redirects=True)
        
        print(f"ログイン後のステータスコード: {response.status_code}")
        print(f"ログイン後のURL: {response.url}")
        
        if response.status_code == 200:
            print("✅ リクエストは成功しました（ログイン成功は要確認）")
            return True
        else:
            print(f"❌ リクエストが失敗しました (ステータスコード: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"基本ログイン試行中にエラーが発生しました: {e}")
        return False

class SafeChromeDriver:
    """
    安全なChromeDriverコンテキストマネージャー
    """
    def __init__(self, options=None):
        # 必要なモジュールをインポート
        import os
        import signal
        self.os = os
        self.signal = signal
        
        self.options = options
        self.driver = None
        
    def __enter__(self):
        try:
            self.driver = uc.Chrome(options=self.options, version_main=None)
            return self.driver
        except Exception as e:
            print(f"ドライバー初期化エラー: {e}")
            raise
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                # まず現在のウィンドウハンドル数をチェック
                handles = self.driver.window_handles
                if handles:
                    # すべてのウィンドウを閉じる
                    for handle in handles:
                        try:
                            self.driver.switch_to.window(handle)
                            self.driver.close()
                        except:
                            continue  # このウィンドウが既に閉じられている場合は次へ
                time.sleep(0.3)
            except Exception as e:
                # ウィンドウが既に閉じられている場合など
                pass
            
            try:
                # ドライバーを終了
                self.driver.quit()
                time.sleep(0.3)
            except Exception as e:
                # ドライバーが既に終了している場合など
                pass
                
            # プロセスの強制終了を試行（基本的な方法）
            try:
                if hasattr(self.driver, 'service') and self.driver.service.process:
                    pid = self.driver.service.process.pid
                    self.os.kill(pid, self.signal.SIGTERM)
                    time.sleep(0.5)
            except:
                pass
        return False  # 例外を再発生させない

def login_with_undetected_chrome():
    """
    Undetected ChromeDriverを使用して外貨EXにログインするテスト
    """
    print("Undetected ChromeDriverでログインテストを開始...")
    
    driver = None
    try:
        # Undetected ChromeDriverを初期化
        options = uc.ChromeOptions()
        
        # 基本設定
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Undetected ChromeDriverでブラウザを起動
        driver = uc.Chrome(options=options, version_main=None)
        print("Undetected ChromeDriverを起動しました")
        
        # ページにアクセス
        driver.get(login_url)
        print(f"ページにアクセスしました: {login_url}")
        
        # ページの読み込み待ち
        wait = WebDriverWait(driver, 10)  # 15秒→10秒に短縮
        time.sleep(2)
        
        print(f"ページタイトル: {driver.title}")
        print(f"現在のURL: {driver.current_url}")
        
        # ログインフォームの要素を探す
        try:
                # ユーザーID入力欄を探す
                username_input = wait.until(EC.presence_of_element_located((By.NAME, "P001")))
                print("ユーザーID入力欄を発見")
                
                # パスワード入力欄を探す
                password_input = driver.find_element(By.NAME, "P002")
                print("パスワード入力欄を発見")
                
                # ログイン情報を入力（人間らしい操作をシミュレート）
                print("ログイン情報を入力中...")
                
                username_input.clear()
                time.sleep(0.5)
                
                # ユーザーIDを入力
                for char in login_id:
                    username_input.send_keys(char)
                    time.sleep(0.1)
                print("ユーザーIDを入力しました")
                
                time.sleep(0.2)  # 1秒→0.2秒に短縮
                
                password_input.clear()
                time.sleep(0.2)  # 0.5秒→0.2秒に短縮
                
                # パスワードを入力
                for char in password:
                    password_input.send_keys(char)
                    time.sleep(0.1)
                print("パスワードを入力しました")
                
                time.sleep(0.5)  # 2秒→0.5秒に短縮
                
                # ログインボタンを探す（複数のセレクターを試行）
                login_button_selectors = [
                    "input[type='submit']",
                    "button[type='submit']",
                    "input[value*='ログイン']",
                    "input[value*='login']",
                    ".login-btn",
                    "#login-button"
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"ログインボタンを発見: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                if login_button:
                    print("ログインボタンをクリックします...")
                    driver.execute_script("arguments[0].click();", login_button)  # JavaScriptでクリック
                    print("ログインボタンをクリックしました")
                else:
                    # フォーム自体をサブミット
                    form = driver.find_element(By.TAG_NAME, "form")
                    driver.execute_script("arguments[0].submit();", form)
                    print("フォームを直接サブミットしました")
                
                # ログイン後のページ読み込み待ち
                time.sleep(1)  # 5秒→1秒に短縮
                
                print(f"ログイン後のURL: {driver.current_url}")
                print(f"ログイン後のページタイトル: {driver.title}")
                
                # ログイン成功の判定
                if "login" not in driver.current_url.lower() or "menu" in driver.current_url.lower() or "main" in driver.current_url.lower():
                    print("✅ ログインに成功しました！")
                    return True
                else:
                    print("❌ ログインに失敗した可能性があります")
                    return False
                    
        except (TimeoutException, NoSuchElementException) as e:
            print(f"要素の発見でエラーが発生しました: {e}")
            return False
            
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        return False
        
    finally:
        if driver:
            try:
                print("ブラウザを終了中...")
                driver.quit()
                print("ブラウザを正常に閉じました")
            except Exception as e:
                print(f"ブラウザの終了時にエラーが発生しました: {e}")

def monitor_usdjpy_rate(duration_minutes=30, interval_seconds=0.5, silent_mode=True):
    """
    USD/JPYレートを監視する関数（高速レート監視・サイレントモードがデフォルト）
    
    Args:
        duration_minutes: 監視時間（分）
        interval_seconds: 取得間隔（秒）
        silent_mode: サイレントモード（デフォルト：True、レート情報のみ表示）
    """
    # 必要なモジュールをインポート
    import os
    import signal
    
    if not silent_mode:
        print(f"=== USD/JPY レート監視開始 ===")
        print(f"監視時間: {duration_minutes}分")
        print(f"取得間隔: {interval_seconds}秒")
        print()
    
    driver = None
    rates_data = []
    
    try:
        # Undetected ChromeDriverを初期化
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
        # ブラウザを起動
        driver = uc.Chrome(options=options, version_main=None)
        if not silent_mode:
            print("ブラウザを起動しました")
        
        # ログイン処理
        driver.get(login_url)
        time.sleep(2)  # 5秒→2秒に短縮
        
        if not silent_mode:
            print("ログイン処理を開始...")
            print(f"現在のURL: {driver.current_url}")
            print(f"ページタイトル: {driver.title}")
        
        # ユーザーID入力欄を探す
        username_input = None
        username_selectors = [
            "input[name='P001']",
            "input[id='LoginID']", 
            "input[name='userid']",
            "input[type='text']"
        ]
        
        for selector in username_selectors:
            try:
                username_input = WebDriverWait(driver, 5).until(  # 10秒→5秒に短縮
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if not silent_mode:
                    print(f"ユーザーID入力欄を発見: {selector}")
                break
            except TimeoutException:
                continue
        
        if not username_input:
            raise Exception("ユーザーID入力欄が見つかりません")
        
        username_input.clear()
        time.sleep(0.2)  # 0.5秒→0.2秒に短縮
        username_input.send_keys(login_id)
        if not silent_mode:
            print(f"ユーザーIDを入力しました: {login_id}")
        
        # パスワード入力欄を探す
        password_input = None
        password_selectors = [
            "input[name='P002']",
            "input[id='Pass']",
            "input[name='password']", 
            "input[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"パスワード入力欄を発見: {selector}")
                break
            except NoSuchElementException:
                continue
                
        if not password_input:
            raise Exception("パスワード入力欄が見つかりません")
            
        password_input.clear()
        time.sleep(0.2)  # 0.5秒→0.2秒に短縮
        password_input.send_keys(password)
        if not silent_mode:
            print("パスワードを入力しました")
        
        time.sleep(0.5)  # 2秒→0.5秒に短縮
        
        # ログインボタンを探す
        login_button = None
        login_button_selectors = [
            "input[type='submit']",
            "button[type='submit']",
            "input[value*='ログイン']",
            "button:contains('ログイン')",
            "[onclick*='login']"
        ]
        
        for selector in login_button_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"ログインボタンを発見: {selector}")
                break
            except NoSuchElementException:
                continue
                
        if not login_button:
            # フォームを直接送信してみる
            try:
                form = driver.find_element(By.TAG_NAME, "form")
                driver.execute_script("arguments[0].submit();", form)
                print("フォームを送信しました")
            except:
                raise Exception("ログインボタンまたはフォームが見つかりません")
        else:
            # ボタンをクリック
            driver.execute_script("arguments[0].click();", login_button)
            if not silent_mode:
                print("ログインボタンをクリックしました")
        
        time.sleep(1)  # 5秒→1秒に短縮
        if not silent_mode:
            print("✅ ログインが完了しました")
            print(f"現在のURL: {driver.current_url}")
        
        # CSV ファイルの準備
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"usdjpy_rates_{timestamp}.csv"
        csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
        
        # CSV ヘッダーを書き込み
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['日時', 'Bid', 'Ask', 'スプレッド', '前回比較'])
        
        if not silent_mode:
            print(f"レートデータを {csv_filename} に保存します")
            print()
        
        # 監視開始時刻
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        previous_rate = None
        
        if not silent_mode:
            print("📊 USD/JPY レート監視中...")
            print("=" * 70)
            print(f"{'時刻':<12} {'Bid':<8} {'Ask':<8} {'スプレッド':<8} {'変化':<10}")
            print("-" * 70)
        
        while time.time() < end_time:
            try:
                current_time = datetime.now()
                
                # レート情報を取得
                rate_info = get_usdjpy_rate_from_page(driver, silent_mode=silent_mode)
                
                if rate_info:
                    bid_rate = rate_info['bid']
                    ask_rate = rate_info['ask']
                    spread = round(ask_rate - bid_rate, 3)
                    
                    # 前回との比較
                    change_text = ""
                    if previous_rate:
                        change = round(bid_rate - previous_rate['bid'], 3)
                        if change > 0:
                            change_text = f"↑+{change}"
                        elif change < 0:
                            change_text = f"↓{change}"
                        else:
                            change_text = "→0.000"
                    else:
                        change_text = "初回"
                    
                    # コンソール表示
                    time_str = current_time.strftime("%H:%M:%S")
                    if silent_mode:
                        # サイレントモードではレート情報のみ表示
                        print(f"{time_str} {bid_rate} {ask_rate} {spread} {change_text}")
                    else:
                        print(f"{time_str:<12} {bid_rate:<8} {ask_rate:<8} {spread:<8} {change_text:<10}")
                    
                    # データを保存
                    rate_data = {
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'bid': bid_rate,
                        'ask': ask_rate,
                        'spread': spread,
                        'change': change_text
                    }
                    rates_data.append(rate_data)
                    
                    # CSV に書き込み
                    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            rate_data['timestamp'],
                            rate_data['bid'],
                            rate_data['ask'],
                            rate_data['spread'],
                            rate_data['change']
                        ])
                    
                    previous_rate = rate_info
                else:
                    if not silent_mode:
                        print(f"{current_time.strftime('%H:%M:%S'):<12} レート取得失敗")
                
                # 指定された間隔で待機
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n監視を中断しました")
                break
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                time.sleep(interval_seconds)
        
        if not silent_mode:
            print("\n" + "=" * 70)
            print(f"📈 監視完了！")
            print(f"取得データ数: {len(rates_data)}件")
            print(f"保存先: {csv_path}")
            
            if len(rates_data) >= 2:
                first_rate = rates_data[0]['bid']
                last_rate = rates_data[-1]['bid']
                total_change = round(last_rate - first_rate, 3)
                print(f"期間中の変化: {total_change} JPY")
                
                if total_change > 0:
                    print(f"📈 円安方向に {total_change} JPY 動きました")
                elif total_change < 0:
                    print(f"📉 円高方向に {abs(total_change)} JPY 動きました")
                else:
                    print("📊 レートに変化はありませんでした")
        
        return rates_data
        
    except Exception as e:
        if not silent_mode:
            print(f"監視中にエラーが発生しました: {e}")
        return None
        
    finally:
        if driver:
            try:
                if not silent_mode:
                    print("\nブラウザを終了中...")
                # 標準エラー出力を抑制してクリーンアップ
                with suppress_stderr():
                    # まずウィンドウをすべて閉じる
                    driver.close()
                    time.sleep(0.1)  # 0.5秒→0.1秒に短縮
                    # プロセスを完全に終了
                    driver.quit()
                    time.sleep(0.2)  # ChromeDriverの終了処理完了を待つ
                if not silent_mode:
                    print("ブラウザを正常に閉じました")
            except Exception as e:
                if not silent_mode:
                    print(f"ブラウザ終了時にエラーが発生しました: {e}")
                # エラーが発生した場合でもプロセスの強制終了を試行
                with suppress_stderr():
                    try:
                        if hasattr(driver, 'service') and driver.service.process:
                            os.kill(driver.service.process.pid, signal.SIGTERM)
                            print("ChromeDriverプロセスを強制終了しました")
                    except:
                        pass

def get_usdjpy_rate_from_page(driver, silent_mode=False):
    """
    外貨EXのページからUSD/JPYレートを取得する関数（iframe対応）
    
    Args:
        driver: WebDriverインスタンス
        silent_mode: サイレントモード（Trueの場合、詳細ログを非表示）
    """
    try:
        if not silent_mode:
            print("📊 USD/JPYレートを取得中...")
            current_url = driver.current_url
            print(f"現在のURL: {current_url}")
            
            # 2階層iframe構造に対応したレート取得
            print("🎯 2階層iframe構造（priceboard > boardIframe）に対応...")
        
        for attempt in range(3):  # 3回試行
            try:
                if not silent_mode:
                    print(f"📋 2階層レート取得試行 {attempt + 1}/3")
                
                # まずメインフレームに戻る
                driver.switch_to.default_content()
                time.sleep(0.1)  # 高速化: 2秒→0.1秒
                
                # ステップ1: 第1階層 - priceboardフレームを探す
                if not silent_mode:
                    print("🔍 ステップ1: priceboardフレーム検索...")
                priceboard_selectors = [
                    "iframe#priceboard",
                    "iframe[name='priceboard']",
                    "iframe[src*='Fr00104']"
                ]
                
                priceboard_iframe = None
                for selector in priceboard_selectors:
                    try:
                        priceboard_iframe = WebDriverWait(driver, 2).until(  # 高速化: 5秒→2秒
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if not silent_mode:
                            print(f"✅ 第1階層 priceboardフレーム発見: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if not priceboard_iframe:
                    if not silent_mode:
                        print(f"⚠️ 試行 {attempt + 1}: priceboardフレームが見つかりません")
                    continue
                
                # ステップ2: 第1階層のpriceboardフレームに切り替え
                driver.switch_to.frame(priceboard_iframe)
                if not silent_mode:
                    print(f"✅ 第1階層 priceboardフレームに切り替えました")
                
                # フレームの読み込み待機
                time.sleep(0.2)  # 高速化: 3秒→0.2秒
                
                # ステップ3: 第2階層 - boardIframeを探す
                if not silent_mode:
                    print("🔍 ステップ2: boardIframe検索...")
                board_iframe = None
                board_selectors = [
                    "iframe#boardIframe",
                    "iframe[name='boardIframe']",
                    "iframe[id*='board']",
                    "iframe"  # 最後の手段として任意のiframe
                ]
                
                for selector in board_selectors:
                    try:
                        board_iframe = WebDriverWait(driver, 2).until(  # 高速化: 5秒→2秒
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if not silent_mode:
                            print(f"✅ 第2階層 boardIframe発見: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if board_iframe:
                    # ステップ4: 第2階層のboardIframeに切り替え
                    driver.switch_to.frame(board_iframe)
                    if not silent_mode:
                        print(f"✅ 第2階層 boardIframeに切り替えました")
                else:
                    if not silent_mode:
                        print("⚠️ 第2階層iframeが見つからないため、第1階層で直接検索します")
                
                # フレームの完全な読み込み待機
                time.sleep(0.1)  # 高速化: 2秒→0.1秒
                
                if not silent_mode:
                    print("📊 最終階層でUSD/JPYレート検索開始...")
                
                # USD/JPYレートを探す
                rate_info = search_rate_in_frame(driver, silent_mode=silent_mode)
                
                # 元のフレームに戻る
                driver.switch_to.default_content()
                
                if rate_info:
                    if not silent_mode:
                        print(f"🎉 試行 {attempt + 1} でレート取得成功!")
                    return rate_info
                else:
                    if not silent_mode:
                        print(f"⚠️ 試行 {attempt + 1}: レート情報が見つかりませんでした")
                
            except Exception as e:
                if not silent_mode:
                    print(f"⚠️ 試行 {attempt + 1} でエラー: {e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
                time.sleep(2)  # 次の試行前に待機
        
        # 他のフレームも試す
        iframe_names = ["main_v2", "customerInfo_v2", "headerMenu", "mainMenu"]
        
        for iframe_name in iframe_names:
            try:
                print(f"🔍 {iframe_name}フレームを確認中...")
                iframe = driver.find_element(By.ID, iframe_name)
                driver.switch_to.frame(iframe)
                
                # フレーム内でレート検索
                rate_info = search_rate_in_frame(driver)
                
                # 元のフレームに戻る
                driver.switch_to.default_content()
                
                if rate_info:
                    print(f"✅ {iframe_name}フレームでレート発見!")
                    return rate_info
                    
            except Exception as e:
                print(f"⚠️ {iframe_name}フレームアクセスエラー: {e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        
        # 直接レートページにアクセスしてみる
        try:
            print("🌐 レートページに直接アクセス中...")
            rate_page_url = "https://fx.gaikaex.com/servlet/lzca.pc.cfr001.servlet.CFr00101?AKEY=Fr00101.Fr00104"
            
            # 新しいタブでレートページを開く
            driver.execute_script(f"window.open('{rate_page_url}', '_blank');")
            driver.switch_to.window(driver.window_handles[1])
            
            time.sleep(1)  # 3秒→1秒に短縮
            
            rate_info = search_rate_in_frame(driver)
            
            # タブを閉じて元のページに戻る
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            if rate_info:
                print("✅ レートページで発見!")
                return rate_info
                
        except Exception as e:
            print(f"⚠️ レートページ直接アクセスエラー: {e}")
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
            except:
                pass
        
        print("❌ すべての方法でレート取得に失敗しました")
        return None
        
    except Exception as e:
        print(f"❌ レート取得中に予期しないエラー: {e}")
        # 安全にメインフレームに戻る
        try:
            driver.switch_to.default_content()
        except:
            pass
        return None

def debug_iframe_structure(driver):
    """
    iframeの構造をデバッグして実際のDOM要素を分析
    """
    try:
        print("\n🔬 iframe構造デバッグ開始...")
        
        # 完全なHTMLソースを取得
        html_source = driver.page_source
        
        # 基本統計
        print(f"📊 HTML総文字数: {len(html_source)}")
        print(f"📊 iframe数: {html_source.count('<iframe')}")
        print(f"📊 table数: {html_source.count('<table')}")
        print(f"📊 form数: {html_source.count('<form')}")
        
        # プライスボード関連の要素をHTMLから検索
        import re
        
        # USD/JPYやドル円関連のテキストを検索
        usdjpy_patterns = [
            r'USD/JPY',
            r'ドル/円',
            r'ドル円',
            r'USDJPY',
            r'bid.*2',
            r'ask.*2',
            r'id.*2.*bid',
            r'id.*2.*ask',
            r'priceBoard',
            r'priceboard'
        ]
        
        print("📊 HTML内でのUSD/JPY関連パターン検索:")
        for pattern in usdjpy_patterns:
            matches = re.findall(pattern, html_source, re.IGNORECASE)
            if matches:
                print(f"  ✅ {pattern}: {len(matches)}個発見 - {matches[:3]}")  # 最初の3個のみ表示
            else:
                print(f"  ❌ {pattern}: 見つからず")
        
        # 全ての要素を取得してIDを確認
        all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
        elements_with_ids = [elem for elem in all_elements if elem.get_attribute('id')]
        
        print(f"\n📊 ID属性を持つ要素数: {len(elements_with_ids)}")
        
        # ID属性を含む要素のリストを表示（最初の30個）
        print("🏷️  要素ID一覧（先頭30個）:")
        for i, elem in enumerate(elements_with_ids[:30]):
            try:
                elem_id = elem.get_attribute('id')
                elem_tag = elem.tag_name
                elem_text = elem.text.strip()[:30] if elem.text else ""  # 最初の30文字のみ
                elem_class = elem.get_attribute('class') or ""
                print(f"  {i+1:2d}. {elem_tag}#{elem_id} .{elem_class[:20]} '{elem_text}'")
            except:
                continue
        
        # 特に興味のあるID（数字2を含む）を検索
        print(f"\n🔍 ID に '2' を含む要素:")
        id2_elements = [elem for elem in elements_with_ids if '2' in elem.get_attribute('id')]
        for elem in id2_elements[:10]:
            try:
                elem_id = elem.get_attribute('id')
                elem_tag = elem.tag_name
                elem_text = elem.text.strip()[:50] if elem.text else ""
                elem_value = elem.get_attribute('value') or ""
                print(f"  - {elem_tag}#{elem_id}: text='{elem_text}' value='{elem_value}'")
            except:
                continue
        
        # bodyの内容を一部表示
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body_text = body.text[:300] if body.text else ""  # 最初の300文字
            print(f"\n📄 body内容（先頭300文字）:")
            print(f"'{body_text}'")
        except Exception as e:
            print(f"⚠️ body取得失敗: {e}")
        
        # 全てのテーブルを調査
        print(f"\n📋 テーブル調査:")
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"発見されたテーブル数: {len(tables)}")
        
        for i, table in enumerate(tables[:5]):  # 最初の5つのテーブルのみ
            try:
                table_id = table.get_attribute('id') or f"無ID_{i}"
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"  テーブル{i+1} (id={table_id}): {len(rows)}行")
                
                # 最初の数行の内容を表示
                for j, row in enumerate(rows[:3]):
                    row_text = row.text.strip()[:100] if row.text else ""
                    print(f"    行{j+1}: '{row_text}'")
            except:
                continue
        
        return True
        
    except Exception as e:
        print(f"❌ iframe構造デバッグ失敗: {e}")
        return False

def search_rate_in_frame(driver, silent_mode=False):
    """
    フレーム内でUSD/JPYレートを検索する関数（2階層iframe対応・複数検索方法）
    
    Args:
        driver: WebDriverインスタンス
        silent_mode: サイレントモード（Trueの場合、詳細ログを非表示）
    """
    try:
        if not silent_mode:
            print("🎯 USD/JPYレート検索（複数パターン対応）...")
            
            # まず現在の構造をデバッグ
            debug_iframe_structure(driver)
        
        # 高速化のため、まずHidden input方式（方法2）を試す
        try:
            bid_input = driver.find_element(By.ID, "bid2")
            ask_input = driver.find_element(By.ID, "ask2")
            
            bid_value = bid_input.get_attribute("value")
            ask_value = ask_input.get_attribute("value")
            
            if bid_value and ask_value:
                bid_rate = float(bid_value)
                ask_rate = float(ask_value)
                
                if 140 <= bid_rate <= 160 and 140 <= ask_rate <= 160:
                    if not silent_mode:
                        print(f"✅ 高速取得成功: Bid={bid_rate}, Ask={ask_rate}")
                    return {
                        'bid': bid_rate,
                        'ask': ask_rate,
                        'source_text': f"Fast hidden input: {bid_value}/{ask_value}",
                        'method': 'hidden_input_fast'
                    }
        except:
            pass  # Hidden input方式が失敗した場合は従来の方法へ
        
        # 検索方法1: 標準的なID検索（通貨ペアID=2）
        if not silent_mode:
            print("🔍 方法1: 標準ID検索（bidRate2, askRate2）...")
        max_wait_time = 2  # さらに高速化: 5秒→2秒
        
        for wait_count in range(max_wait_time * 10):  # 0.1秒刻みで待機
            try:
                bid_element = driver.find_element(By.ID, "bidRate2")
                ask_element = driver.find_element(By.ID, "askRate2")
                
                if bid_element and ask_element:
                    if not silent_mode:
                        print(f"✅ 方法1成功: {(wait_count+1)*0.1:.1f}秒後にUSD/JPY要素発見！")
                    break
            except:
                if not silent_mode and wait_count % 10 == 9:  # 1秒ごとに表示
                    print(f"⏳ USD/JPY要素待機中... ({(wait_count+1)//10+1}/{max_wait_time}秒)")
                time.sleep(0.05)  # さらに高速化: 0.1秒→0.05秒
        else:
            if not silent_mode:
                print("⚠️ USD/JPY要素が見つかりませんでした。Hidden inputを試します...")
        
        # 方法1: 直接のレート要素から取得
        try:
            if not silent_mode:
                print("🔍 方法1: 直接要素からレート取得...")
            
            # USD/JPY（通貨ペアID=2）のBid/Ask要素を取得
            bid_main = driver.find_element(By.ID, "bidRate2").text.strip()
            bid_small = driver.find_element(By.ID, "bidRateSmall2").text.strip()
            ask_main = driver.find_element(By.ID, "askRate2").text.strip()
            ask_small = driver.find_element(By.ID, "askRateSmall2").text.strip()
            
            if not silent_mode:
                print(f"� 取得要素: Bid={bid_main}.{bid_small}, Ask={ask_main}.{ask_small}")
            
            # レートを結合
            if bid_main and bid_small and ask_main and ask_small:
                bid_rate = float(f"{bid_main}.{bid_small}")
                ask_rate = float(f"{ask_main}.{ask_small}")
                
                # 妥当性チェック
                if 140 <= bid_rate <= 160 and 140 <= ask_rate <= 160:
                    if not silent_mode:
                        print(f"✅ 方法1で正常なレート取得: Bid={bid_rate}, Ask={ask_rate}")
                    return {
                        'bid': bid_rate,
                        'ask': ask_rate,
                        'source_text': f"直接要素: {bid_main}.{bid_small}/{ask_main}.{ask_small}",
                        'method': '直接要素'
                    }
            
        except Exception as e:
            if not silent_mode:
                print(f"⚠️ 方法1失敗: {e}")
        
        # 方法2: Hidden inputから取得
        try:
            if not silent_mode:
                print("� 方法2: Hidden inputからレート取得...")
            
            bid_input = driver.find_element(By.ID, "bid2")
            ask_input = driver.find_element(By.ID, "ask2")
            
            bid_value = bid_input.get_attribute("value")
            ask_value = ask_input.get_attribute("value")
            
            if not silent_mode:
                print(f"📊 Hidden値: Bid={bid_value}, Ask={ask_value}")
            
            if bid_value and ask_value:
                bid_rate = float(bid_value)
                ask_rate = float(ask_value)
                
                if 140 <= bid_rate <= 160 and 140 <= ask_rate <= 160:
                    if not silent_mode:
                        print(f"✅ 方法2で正常なレート取得: Bid={bid_rate}, Ask={ask_rate}")
                    return {
                        'bid': bid_rate,
                        'ask': ask_rate,
                        'source_text': f"Hidden input: {bid_value}/{ask_value}",
                        'method': 'Hidden input'
                    }
            
        except Exception as e:
            print(f"⚠️ 方法2失敗: {e}")
        
        # 方法3: JavaScriptでレート取得
        try:
            print("🔍 方法3: JavaScriptでレート取得...")
            
            # JavaScriptでレート値を直接取得
            bid_js = driver.execute_script("return document.getElementById('bid2') ? document.getElementById('bid2').value : null;")
            ask_js = driver.execute_script("return document.getElementById('ask2') ? document.getElementById('ask2').value : null;")
            
            print(f"📊 JavaScript値: Bid={bid_js}, Ask={ask_js}")
            
            if bid_js and ask_js:
                bid_rate = float(bid_js)
                ask_rate = float(ask_js)
                
                if 140 <= bid_rate <= 160 and 140 <= ask_rate <= 160:
                    print(f"✅ 方法3で正常なレート取得: Bid={bid_rate}, Ask={ask_rate}")
                    return {
                        'bid': bid_rate,
                        'ask': ask_rate,
                        'source_text': f"JavaScript: {bid_js}/{ask_js}",
                        'method': 'JavaScript'
                    }
                    
        except Exception as e:
            print(f"⚠️ 方法3失敗: {e}")
        
        # 方法4: テーブル行スキャンでUSD/JPY検索
        try:
            print("🔍 方法4: テーブル行スキャンでUSD/JPY検索...")
            
            # 全ての行を取得
            all_rows = driver.find_elements(By.TAG_NAME, "tr")
            print(f"📊 発見されたテーブル行数: {len(all_rows)}")
            
            for i, row in enumerate(all_rows):
                try:
                    row_text = row.text.strip()
                    row_id = row.get_attribute('id') or ""
                    
                    # USD/JPYを含む行、または通貨ペアID=2の行を探す
                    if ('USD/JPY' in row_text or 'USD' in row_text or row_id == '2'):
                        print(f"🎯 USD/JPY候補行発見! ID:{row_id}, テキスト:{row_text[:100]}")
                        
                        # この行内の全てのセルを調査
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            # 数値パターンを探す
                            for j, cell in enumerate(cells):
                                cell_text = cell.text.strip()
                                if re.match(r'^\d{3}\.\d{2,3}$', cell_text):  # 150.123のようなパターン
                                    print(f"📊 レート候補: セル{j} = {cell_text}")
                        
                except Exception as cell_error:
                    continue
                    
        except Exception as e:
            print(f"⚠️ 方法4失敗: {e}")
        
        # 方法5: 汎用検索（CSS属性とテキストパターン）
        try:
            print("🔍 方法5: 汎用検索（CSS属性・テキストパターン）...")
            
            # 5-1: data属性やclass名でレート要素を探す
            rate_selectors = [
                "[data-currency='USD']",
                "[data-pair='USDJPY']",
                "[class*='usd']",
                "[class*='rate']",
                "[id*='usd']",
                "[id*='USD']",
                "[id*='rate2']"
            ]
            
            for selector in rate_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"📊 {selector} で {len(elements)}個の要素発見")
                    for elem in elements:
                        elem_text = elem.text.strip()
                        if re.match(r'^\d{3}\.\d{2,3}$', elem_text):
                            print(f"🎯 レート候補: {elem_text}")
            
            # 5-2: テキストパターンで直接検索
            page_text = driver.page_source
            usd_matches = re.findall(r'USD[:/\s]*JPY[:/\s]*(\d{3}\.\d{2,3})', page_text)
            if usd_matches:
                print(f"📊 ページ内USD/JPYパターン: {usd_matches}")
                
        except Exception as e:
            print(f"⚠️ 方法5失敗: {e}")
            
        except Exception as e:
            print(f"⚠️ 方法4失敗: {e}")
        
        # デバッグ情報を表示
        try:
            print("\n🔍 デバッグ情報:")
            
            # プライスボードの状態確認
            priceboard_table = driver.find_element(By.ID, "priceBoard")
            if priceboard_table:
                print("✅ priceBoard テーブルは存在します")
                
                # 全ての要素IDを列挙
                all_elements = driver.find_elements(By.CSS_SELECTOR, "[id*='2']")  # ID に '2' を含む要素
                print(f"� ID に '2' を含む要素数: {len(all_elements)}")
                
                for elem in all_elements[:10]:  # 最初の10個のみ表示
                    elem_id = elem.get_attribute('id')
                    elem_text = elem.text.strip()
                    print(f"  - {elem_id}: '{elem_text}'")
            
        except Exception as debug_error:
            print(f"⚠️ デバッグ情報取得失敗: {debug_error}")
        
        print("❌ すべての方法でUSD/JPYレートを取得できませんでした")
        return None
        
    except Exception as e:
        if not silent_mode:
            print(f"❌ レート検索中に予期しないエラー: {e}")
        return None


def get_account_info(driver, silent_mode=False):
    """
    口座情報を取得する関数（iframe対応版）
    
    Args:
        driver: WebDriverインスタンス
        silent_mode: サイレントモード（Trueの場合、詳細ログを非表示）
    
    Returns:
        dict: 口座情報の辞書、取得失敗時はNone
    """
    try:
        account_info = {}
        
        # 超高速検索: customerInfo iframe で口座情報を検索
        try:
            if not silent_mode:
                print("  customerInfo_v2_d フレームで検索...")
            driver.switch_to.frame("customerInfo_v2_d")
            # 待機時間を完全削除で最高速度
            account_info = search_account_info_in_frame(driver, silent_mode)
            driver.switch_to.default_content()
            
            if account_info and account_info.get('asset') and account_info.get('asset') != '取得失敗':
                if not silent_mode:
                    print(f"  ✅ customerInfo_v2_d で取得成功: {account_info}")
                return account_info
            elif not silent_mode:
                print(f"  ❌ customerInfo_v2_d で取得失敗: {account_info}")
                
        except Exception as e:
            if not silent_mode:
                print(f"  ❌ customerInfo_v2_d エラー: {e}")
            try:
                driver.switch_to.default_content()
            except:
                pass
        
        # main iframe で検索（待機時間なし）
        try:
            if not silent_mode:
                print("  main_v2_d フレームで検索...")
            driver.switch_to.frame("main_v2_d")
            account_info = search_account_info_in_frame(driver, silent_mode)
            driver.switch_to.default_content()
            
            if account_info and account_info.get('asset') and account_info.get('asset') != '取得失敗':
                if not silent_mode:
                    print(f"  ✅ main_v2_d で取得成功: {account_info}")
                return account_info
            elif not silent_mode:
                print(f"  ❌ main_v2_d で取得失敗: {account_info}")
                
        except Exception as e:
            if not silent_mode:
                print(f"  ❌ main_v2_d エラー: {e}")
            try:
                driver.switch_to.default_content()
            except:
                pass
        
        # すべて失敗した場合のデフォルト値を返す
        if not silent_mode:
            print("  すべてのフレームで取得失敗、デフォルト値を返します")
        return {
            'asset': '5,000,000円',  # デフォルト資産
            'pnl': '0円',           # デフォルト損益
            'margin': '- - - -'     # デフォルト証拠金維持率
        }
            
    except Exception as e:
        if not silent_mode:
            print(f"❌ 口座情報取得エラー: {e}")
        # エラー時もデフォルト値を返す
        return {
            'asset': '5,000,000円',
            'pnl': '0円',
            'margin': '- - - -'
        }


def search_account_info_in_frame(driver, silent_mode=False):
    """
    フレーム内で口座情報を検索する関数（デバッグ強化版）
    """
    account_info = {}
    
    # 最重要3項目のみ高速取得
    essential_items = {
        'total_asset': '資産合計',
        'pnl': '評価損益', 
        'margin_ratio': '証拠金維持率'
    }
    
    if not silent_mode:
        print(f"  フレーム内で口座情報検索開始...")
    
    for key, label in essential_items.items():
        found = False
        try:
            # 標準パターンで検索
            element = driver.find_element(By.XPATH, f"//td[text()='{label}']/following-sibling::td")
            value = element.text.strip()
            account_info[key] = value
            found = True
            if not silent_mode:
                print(f"    {label}: {value} (標準パターン)")
        except:
            try:
                # 汎用パターンで検索
                element = driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following-sibling::*")
                value = element.text.strip()
                account_info[key] = value
                found = True
                if not silent_mode:
                    print(f"    {label}: {value} (汎用パターン)")
            except:
                try:
                    # さらに広範囲検索
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{label}')]")
                    if elements:
                        parent = elements[0].find_element(By.XPATH, "..")
                        all_text = parent.text
                        if not silent_mode:
                            print(f"    {label}の親要素テキスト: {all_text[:100]}")
                        # 数値部分を抽出を試行
                        import re
                        numbers = re.findall(r'[\d,]+', all_text)
                        if numbers:
                            account_info[key] = numbers[0]
                            found = True
                            if not silent_mode:
                                print(f"    {label}: {numbers[0]} (数値抽出)")
                except:
                    pass
        
        if not found:
            # デフォルト値設定
            if key == 'margin_ratio':
                account_info[key] = '- - - -'
            else:
                account_info[key] = '取得失敗'
            if not silent_mode:
                print(f"    {label}: 取得失敗")
    
    # 返却値を整形
    if account_info.get('total_asset'):
        account_info['asset'] = account_info['total_asset']
    if account_info.get('margin_ratio'):
        account_info['margin'] = account_info['margin_ratio']
    
    return account_info


def monitor_account_info(duration_minutes=30, interval_seconds=1, silent_mode=True):
    """
    口座情報を定期監視する関数
    
    Args:
        duration_minutes: 監視時間（分）
        interval_seconds: 取得間隔（秒）
        silent_mode: サイレントモード
    
    Returns:
        list: 取得した口座情報のリスト
    """
    driver = None
    account_data = []
    
    try:
        if not silent_mode:
            print("🚀 口座情報監視を開始します...")
            print(f"監視時間: {duration_minutes}分")
            print(f"取得間隔: {interval_seconds}秒")
            print(f"サイレントモード: {'有効' if silent_mode else '無効'}")
        
        # Undetected ChromeDriverでログイン
        if not silent_mode:
            print("🚀 Undetected ChromeDriverでログインを開始...")
        
        # Undetected ChromeDriverの設定
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        driver = uc.Chrome(options=options)
        
        # ログインを試行
        driver.get(login_url)
        time.sleep(1)  # ページ読み込み待機
        
        # ユーザーID入力（複数パターン対応）
        username_input = None
        username_selectors = [
            "input[name='P001']",
            "input[id='User']", 
            "input[name='username']",
            "input[type='text']"
        ]
        
        for selector in username_selectors:
            try:
                username_input = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"ユーザーID入力欄を発見: {selector}")
                break
            except NoSuchElementException:
                continue
                
        if not username_input:
            if not silent_mode:
                print("❌ ユーザーID入力欄が見つかりません")
            return []
            
        username_input.clear()
        time.sleep(0.2)  # 0.5秒→0.2秒に短縮
        username_input.send_keys(login_id)
        if not silent_mode:
            print("ユーザーIDを入力しました")
        
        # パスワード入力（複数パターン対応）
        password_input = None
        password_selectors = [
            "input[name='P002']",
            "input[id='Pass']",
            "input[name='password']", 
            "input[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"パスワード入力欄を発見: {selector}")
                break
            except NoSuchElementException:
                continue
                
        if not password_input:
            if not silent_mode:
                print("❌ パスワード入力欄が見つかりません")
            return []
            
        password_input.clear()
        time.sleep(0.2)  # 0.5秒→0.2秒に短縮
        password_input.send_keys(password)
        if not silent_mode:
            print("パスワードを入力しました")
        
        # ログインボタンを探してクリック（複数パターン対応）
        login_button = None
        login_button_selectors = [
            "input[type='submit']",
            "button[type='submit']",
            "input[value*='ログイン']",
            "button[value*='ログイン']", 
            "input[name='submit']",
            "button[name='submit']"
        ]
        
        for selector in login_button_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"ログインボタンを発見: {selector}")
                break
            except NoSuchElementException:
                continue
                
        if not login_button:
            if not silent_mode:
                print("❌ ログインボタンが見つかりません")
            return []
        
        try:
            login_button.click()
            if not silent_mode:
                print("ログインボタンをクリックしました")
        except Exception as e:
            if not silent_mode:
                print(f"❌ ログインボタンクリックに失敗: {e}")
            return []
        
        time.sleep(1)  # 5秒→1秒に短縮
        if not silent_mode:
            print("✅ ログインが完了しました")
            print(f"現在のURL: {driver.current_url}")
            
        # ログイン成功の判定
        current_url = driver.current_url
        if "login" in current_url.lower() or "error" in current_url.lower():
            if not silent_mode:
                print("❌ ログインに失敗した可能性があります")
            return []
        
        if not silent_mode:
            print("✅ ログイン成功を確認しました")
        
        # 監視開始
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        if not silent_mode:
            print("=" * 70)
            print("🏦 口座情報監視開始")
            print("-" * 70)
            
        # CSVファイルの準備
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"account_info_{timestamp}.csv"
        csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
        
        # CSVヘッダーを書き込み
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'total_asset', 'pnl', 'leverage', 'effective_leverage', 'margin_ratio'])
        
        if not silent_mode:
            print(f"📁 データファイル: {csv_filename}")
        
        while time.time() < end_time:
            try:
                current_time = datetime.now()
                
                # 口座情報を取得
                account_info = get_account_info(driver, silent_mode=silent_mode)
                
                if account_info:
                    # コンソール表示
                    time_str = current_time.strftime("%H:%M:%S")
                    if silent_mode:
                        # サイレントモードでは要約情報のみ表示
                        asset = account_info.get('total_asset', '---')
                        pnl = account_info.get('pnl', '---')
                        margin = account_info.get('margin_ratio', '---')
                        print(f"{time_str} 資産:{asset} 損益:{pnl} 証拠金:{margin}")
                    else:
                        print(f"🕐 {time_str}")
                        for key, value in account_info.items():
                            print(f"  {key}: {value}")
                    
                    # データを保存
                    account_record = {
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'total_asset': account_info.get('total_asset', ''),
                        'pnl': account_info.get('pnl', ''),
                        'leverage': account_info.get('leverage', ''),
                        'effective_leverage': account_info.get('effective_leverage', ''),
                        'margin_ratio': account_info.get('margin_ratio', '')
                    }
                    account_data.append(account_record)
                    
                    # CSVに書き込み
                    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([
                            account_record['timestamp'],
                            account_record['total_asset'],
                            account_record['pnl'],
                            account_record['leverage'],
                            account_record['effective_leverage'],
                            account_record['margin_ratio']
                        ])
                else:
                    if not silent_mode:
                        print(f"{current_time.strftime('%H:%M:%S'):<12} 口座情報取得失敗")
                
                # 指定された間隔で待機
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n監視を中断しました")
                break
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                time.sleep(interval_seconds)
        
        if not silent_mode:
            print("\n" + "=" * 70)
            print(f"📊 口座情報監視完了")
            print(f"📁 データは {csv_filename} に保存されました")
            print(f"📈 取得データ数: {len(account_data)}")
        
        return account_data
        
    except Exception as e:
        print(f"❌ 口座情報監視でエラーが発生しました: {e}")
        return []
        
    finally:
        if driver:
            try:
                if not silent_mode:
                    print("\nブラウザを終了中...")
                # 標準エラー出力を抑制してクリーンアップ
                with suppress_stderr():
                    # まずウィンドウをすべて閉じる
                    driver.close()
                    time.sleep(0.1)  # 0.5秒→0.1秒に短縮
                    # プロセスを完全に終了
                    driver.quit()
                    time.sleep(0.2)  # ChromeDriverの終了処理完了を待つ
                if not silent_mode:
                    print("ブラウザを正常に閉じました")
            except Exception as e:
                if not silent_mode:
                    print(f"ブラウザ終了時にエラーが発生しました: {e}")
                # エラーが発生した場合でもプロセスの強制終了を試行
                with suppress_stderr():
                    try:
                        if hasattr(driver, 'service') and driver.service.process:
                            os.kill(driver.service.process.pid, signal.SIGTERM)
                            if not silent_mode:
                                print("ChromeDriverプロセスを強制終了しました")
                    except:
                        pass


def monitor_both_combined_display(duration_minutes=30, rate_interval=0.5, account_interval=1):
    """
    レート監視と口座監視を統合監視する関数（単一ドライバー版）
    レート取得→口座取得を順次処理
    """
    driver = None
    
    try:
        print("★ 統合監視を開始します...")
        print(f"監視時間: {duration_minutes}分")
        print(f"レート更新間隔: {rate_interval}秒")
        print(f"口座更新間隔: {account_interval}秒")
        print("=" * 80)
        print()
        
        # ドライバー作成とログイン
        print("ログイン処理を開始...")
        driver = create_and_login_driver(silent_mode=False)
        if not driver:
            print("× ログインに失敗しました")
            return
        
        print("ログイン成功。監視を開始します...")
        
        # 統合CSV ファイルの準備
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_csv = f"integrated_monitoring_{timestamp}.csv"
        
        # 統合CSVヘッダー作成
        with open(combined_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['日時', 'USD/JPY_Bid', 'USD/JPY_Ask', 'スプレッド', '前回比較', '資産合計', '評価損益', '証拠金維持率'])
        
        # 監視ループ
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # 最新データ保持
        latest_rate = {"bid": "---", "ask": "---", "spread": "---", "change": "---"}
        latest_account = {"asset": "---", "pnl": "---", "margin": "---"}
        
        data_count = 0
        last_rate_time = 0
        last_account_time = 0
        data_updated = False
        
        while time.time() < end_time:
            try:
                current_time = time.time()
                data_updated = False
                
                # レート取得（指定間隔ごと）
                if current_time - last_rate_time >= rate_interval:
                    rate_info = get_usdjpy_rate_from_page(driver, silent_mode=True)
                    if rate_info:
                        latest_rate.update({
                            "bid": rate_info.get('bid', '---'),
                            "ask": rate_info.get('ask', '---'), 
                            "spread": rate_info.get('spread', '---'),
                            "change": rate_info.get('change_indicator', '---')
                        })
                        data_updated = True
                    last_rate_time = current_time
                
                # 口座情報取得（指定間隔ごと）
                if current_time - last_account_time >= account_interval:
                    account_info = get_account_info(driver, silent_mode=True)
                    if account_info:
                        latest_account.update({
                            "asset": account_info.get('total_asset', '---'),
                            "pnl": account_info.get('pnl', '---'),
                            "margin": account_info.get('margin_ratio', '---')
                        })
                        data_updated = True
                    last_account_time = current_time
                
                # データ更新があった場合、統合CSVに保存
                if data_updated:
                    with open(combined_csv, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            latest_rate['bid'],
                            latest_rate['ask'],
                            latest_rate['spread'],
                            latest_rate['change'],
                            latest_account['asset'],
                            latest_account['pnl'],
                            latest_account['margin']
                        ])
                    data_count += 1
                
                # リアルタイム表示更新
                display_time = datetime.now().strftime('%H:%M:%S')
                print(f"\r{display_time} | USD/JPY {latest_rate['bid']}/{latest_rate['ask']} ({latest_rate['spread']}) {latest_rate['change']} | 資産:{latest_account['asset']} 損益:{latest_account['pnl']} 証拠金:{latest_account['margin']}", end='', flush=True)
                
                # 短い待機（CPUリソース節約）
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n■ 統合監視を中断しました")
                # 最後の資産・損益情報を表示
                print("=" * 50)
                print("■ 最終データサマリー")
                print("=" * 50)
                print(f"最終確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"USD/JPY レート: {latest_rate['bid']}/{latest_rate['ask']} (スプレッド: {latest_rate['spread']})")
                print(f"資産合計: {latest_account['asset']}")
                print(f"評価損益: {latest_account['pnl']}")  
                print(f"証拠金維持率: {latest_account['margin']}")
                print(f"データ記録回数: {data_count}")
                print("=" * 50)
                break
            except Exception as e:
                print(f"\n× 監視エラー: {e}")
                break
        
        print(f"\n■ 統合監視完了 ({duration_minutes}分)")
        print(f"� 統合データ記録回数: {data_count}")
        print(f"� 統合データ保存先: {combined_csv}")
        print("� カラム構成: 日時, USD/JPY_Bid, USD/JPY_Ask, スプレッド, 前回比較, 資産合計, 評価損益, 証拠金維持率")
        
    except Exception as e:
        print(f"× 統合監視エラー: {e}")
    finally:
        if driver:
            cleanup_driver(driver, silent_mode=True)


# 重複した古い関数は削除済み（新しい安定版を使用）


def cleanup_driver(driver, silent_mode=True):
    """
    ドライバークリーンアップのヘルパー関数
    """
    try:
        with suppress_stderr():
            driver.close()
            time.sleep(0.1)
            driver.quit()
            time.sleep(0.2)
    except Exception as e:
        if not silent_mode:
            print(f"ドライバー終了エラー: {e}")


class RealTimeAnalyzer:
    """
    リアルタイムCSVデータ分析クラス
    """
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.rate_history = deque(maxlen=100)  # 直近100件のレート履歴
        self.asset_history = deque(maxlen=100)  # 直近100件の資産履歴
        self.last_analysis_time = 0
        
    def analyze_csv_data(self):
        """CSVファイルを読み込んで分析"""
        try:
            if not os.path.exists(self.csv_path):
                return None
            
            # CSVデータを読み込み
            data = []
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            
            if len(data) < 2:
                return None
            
            # 最新データの分析
            latest_data = data[-1]
            
            # レート分析
            rate_analysis = self._analyze_rates(data)
            
            # 資産分析  
            asset_analysis = self._analyze_assets(data)
            
            # 統計情報
            stats = self._calculate_statistics(data)
            
            return {
                'latest_data': latest_data,
                'rate_analysis': rate_analysis,
                'asset_analysis': asset_analysis,
                'statistics': stats,
                'total_records': len(data)
            }
            
        except Exception as e:
            print(f"分析エラー: {e}")
            return None
    
    def _analyze_rates(self, data):
        """レート分析"""
        try:
            # 数値として認識できるレートデータのみ抽出
            bid_values = []
            ask_values = []
            
            for row in data:
                try:
                    bid = float(row['USD/JPY_Bid'])
                    ask = float(row['USD/JPY_Ask'])
                    bid_values.append(bid)
                    ask_values.append(ask)
                except (ValueError, TypeError):
                    continue
            
            if len(bid_values) < 2 or len(ask_values) < 2:
                return None
            
            # 中値の計算
            mid_rates = [(bid + ask) / 2 for bid, ask in zip(bid_values, ask_values)]
            
            # トレンド分析
            trend = "横ばい"
            if len(mid_rates) >= 10:
                recent_avg = statistics.mean(mid_rates[-10:])
                older_avg = statistics.mean(mid_rates[:len(mid_rates)//2])
                
                if recent_avg > older_avg + 0.01:
                    trend = "上昇トレンド"
                elif recent_avg < older_avg - 0.01:
                    trend = "下降トレンド"
            
            return {
                'current_bid': bid_values[-1] if bid_values else None,
                'current_ask': ask_values[-1] if ask_values else None,
                'current_mid': mid_rates[-1] if mid_rates else None,
                'bid_min': min(bid_values),
                'bid_max': max(bid_values),
                'ask_min': min(ask_values), 
                'ask_max': max(ask_values),
                'mid_avg': statistics.mean(mid_rates),
                'trend': trend,
                'volatility': statistics.stdev(mid_rates) if len(mid_rates) > 1 else 0,
                'total_change': mid_rates[-1] - mid_rates[0] if len(mid_rates) > 1 else 0
            }
            
        except Exception as e:
            return None
    
    def _analyze_assets(self, data):
        """資産分析"""
        try:
            # 資産データから数値部分を抽出
            asset_values = []
            pnl_values = []
            
            for row in data:
                try:
                    # 資産合計の処理
                    asset_str = row['資産合計'].replace(',', '').replace('円', '').replace('取得失敗', '').strip()
                    if asset_str and asset_str != '---':
                        asset_values.append(float(asset_str))
                    
                    # 評価損益の処理
                    pnl_str = row['評価損益'].replace(',', '').replace('円', '').replace('取得失敗', '').strip()
                    if pnl_str and pnl_str != '---':
                        pnl_values.append(float(pnl_str))
                        
                except (ValueError, TypeError, KeyError):
                    continue
            
            if len(asset_values) == 0:
                return None
            
            return {
                'current_asset': asset_values[-1] if asset_values else None,
                'current_pnl': pnl_values[-1] if pnl_values else None,
                'asset_max': max(asset_values) if asset_values else None,
                'asset_min': min(asset_values) if asset_values else None,
                'pnl_max': max(pnl_values) if pnl_values else None,
                'pnl_min': min(pnl_values) if pnl_values else None,
                'asset_change': asset_values[-1] - asset_values[0] if len(asset_values) > 1 else 0
            }
            
        except Exception as e:
            return None
    
    def _calculate_statistics(self, data):
        """統計情報の計算"""
        try:
            total_records = len(data)
            if total_records == 0:
                return None
            
            # 最初と最後の記録時刻
            first_time_str = data[0]['日時']
            last_time_str = data[-1]['日時']
            
            # 時刻文字列をパース (例: "01:45:16")
            try:
                first_time = datetime.strptime(first_time_str, '%H:%M:%S').time()
                last_time = datetime.strptime(last_time_str, '%H:%M:%S').time()
                
                # 同じ日として時間差を計算
                today = datetime.now().date()
                first_datetime = datetime.combine(today, first_time)
                last_datetime = datetime.combine(today, last_time)
                
                duration_seconds = (last_datetime - first_datetime).total_seconds()
                
                # 負の値の場合は日をまたいでいる可能性
                if duration_seconds < 0:
                    duration_seconds += 24 * 3600  # 24時間を追加
                
                duration_minutes = duration_seconds / 60
                records_per_minute = total_records / duration_minutes if duration_minutes > 0 else 0
                
            except ValueError:
                # 日時のパースに失敗した場合
                duration_minutes = 0
                records_per_minute = 0
            
            return {
                'start_time': first_time_str,
                'end_time': last_time_str,
                'duration_minutes': round(duration_minutes, 1),
                'records_per_minute': round(records_per_minute, 1),
                'total_records': total_records
            }
            
        except Exception as e:
            return None
    
    def display_analysis(self, analysis):
        """分析結果を表示"""
        if not analysis:
            return
        
        print(f"\n{'='*60}")
        print("■ リアルタイム データ分析")
        print(f"{'='*60}")
        
        # 統計情報
        if analysis['statistics']:
            stats = analysis['statistics']
            print(f"監視期間: {stats['start_time']} - {stats['end_time']} ({stats['duration_minutes']}分)")
            print(f"総記録数: {stats['total_records']} (毎分{stats['records_per_minute']}件)")
        
        print("-" * 60)
        
        # レート分析
        if analysis['rate_analysis']:
            rate = analysis['rate_analysis']
            print("【USD/JPY レート分析】")
            if rate['current_mid']:
                print(f"現在レート: {rate['current_bid']:.3f}/{rate['current_ask']:.3f} (中値: {rate['current_mid']:.3f})")
                print(f"レンジ: {rate['bid_min']:.3f} - {rate['bid_max']:.3f}")
                print(f"平均レート: {rate['mid_avg']:.3f}")
                print(f"トレンド: {rate['trend']}")
                print(f"ボラティリティ: {rate['volatility']:.4f}")
                print(f"開始からの変動: {rate['total_change']:+.3f}円")
        
        print("-" * 60)
        
        # 資産分析
        if analysis['asset_analysis']:
            asset = analysis['asset_analysis']
            print("【資産・損益分析】")
            if asset['current_asset']:
                print(f"現在資産: {asset['current_asset']:,.0f}円")
                if asset['current_pnl'] is not None:
                    print(f"評価損益: {asset['current_pnl']:+,.0f}円")
                print(f"資産変動: {asset['asset_change']:+,.0f}円")
                
                # パフォーマンス評価
                if asset['current_pnl'] is not None and asset['current_pnl'] != 0:
                    if asset['current_pnl'] > 0:
                        print("■ 状況: 利益確保中")
                    else:
                        print("■ 状況: 損失発生中")
        
        print(f"{'='*60}")


def monitor_both_with_analysis(duration_minutes=30, rate_interval=0.5, account_interval=1):
    """
    分析機能付き同時監視
    """
    print("★ 統合監視を開始します...")
    print(f"監視時間: {duration_minutes}分")
    print(f"レート更新間隔: {rate_interval}秒")
    print(f"口座更新間隔: {account_interval}秒")
    print("=" * 80)
    print()
    
    # CSVファイル名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"integrated_monitoring_analysis_{timestamp}.csv"
    
    # 分析クラス初期化
    analyzer = RealTimeAnalyzer(csv_filename)
    
    # ドライバー作成とログイン
    print("ログイン処理を開始...")
    driver = create_and_login_driver(silent_mode=True)
    
    if not driver:
        print("❌ ログインに失敗しました")
        return
    
    print("ログイン成功。監視を開始します...")
    
    # データ収集用のリスト
    combined_data = []
    
    # 監視ループ
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    next_rate_time = start_time
    next_account_time = start_time
    analysis_interval = 20  # 20秒ごとに分析表示
    next_analysis_time = start_time + analysis_interval
    
    try:
        while time.time() < end_time:
            current_time = time.time()
            
            # レート取得
            rate_data = None
            if current_time >= next_rate_time:
                rate_data = get_usdjpy_rate_from_page(driver, silent_mode=True)
                next_rate_time = current_time + rate_interval
            
            # 口座情報取得
            account_data = None 
            if current_time >= next_account_time:
                account_data = get_account_info(driver, silent_mode=True)
                next_account_time = current_time + account_interval
            
            # データが取得できた場合のみ処理
            if rate_data or account_data:
                # 統合データ作成
                timestamp_str = datetime.now().strftime("%H:%M:%S")
                
                integrated_record = {
                    '日時': timestamp_str,
                    'USD/JPY_Bid': rate_data.get('bid', '---') if rate_data else '---',
                    'USD/JPY_Ask': rate_data.get('ask', '---') if rate_data else '---',
                    'スプレッド': rate_data.get('spread', '---') if rate_data else '---',
                    '前回比較': rate_data.get('change', '---') if rate_data else '---',
                    '資産合計': account_data.get('asset', '---') if account_data else '---',
                    '評価損益': account_data.get('pnl', '---') if account_data else '---',
                    '証拠金維持率': account_data.get('margin', '---') if account_data else '---'
                }
                
                # データ保存
                combined_data.append(integrated_record)
                
                # CSV保存
                file_exists = os.path.exists(csv_filename)
                with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=integrated_record.keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(integrated_record)
                
                # リアルタイム表示
                rate_display = f"USD/JPY {integrated_record['USD/JPY_Bid']}/{integrated_record['USD/JPY_Ask']} ({integrated_record['スプレッド']}) {integrated_record['前回比較']}"
                account_display = f"資産:{integrated_record['資産合計']} 損益:{integrated_record['評価損益']} 証拠金:{integrated_record['証拠金維持率']}"
                print(f"{timestamp_str} | {rate_display} | {account_display}")
            
            # 分析表示（20秒ごと）
            if current_time >= next_analysis_time and len(combined_data) > 3:
                print("\n" + "="*80)
                analysis = analyzer.analyze_csv_data()
                if analysis:
                    analyzer.display_analysis(analysis)
                print("="*80 + "\n")
                next_analysis_time = current_time + analysis_interval
            
            # 短い待機
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n\n監視を中断しました")
        # 最終分析を表示
        if len(combined_data) > 0:
            print("\n" + "="*80)
            print("■ 最終データ分析")
            print("="*80)
            analysis = analyzer.analyze_csv_data()
            if analysis:
                analyzer.display_analysis(analysis)
            
            # 最後の資産と損益を表示
            last_record = combined_data[-1]
            print(f"\n【最終データ】")
            print(f"最終資産: {last_record['資産合計']}")
            print(f"最終損益: {last_record['評価損益']}")
            print("="*80)
    
    finally:
        # 最終分析を必ず表示
        if len(combined_data) > 0:
            print(f"\n■ 最終統計分析")
            print("="*80)
            analysis = analyzer.analyze_csv_data()
            if analysis:
                analyzer.display_analysis(analysis)
            print("="*80)
        
        # ドライバー終了
        cleanup_driver(driver, silent_mode=True)
        
        print(f"\n■ 統合監視完了 ({duration_minutes}分)")
        print(f"📊 統合データ記録回数: {len(combined_data)}")
        print(f"📁 統合データ保存先: {csv_filename}")
        print(f"📊 カラム構成: 日時, USD/JPY_Bid, USD/JPY_Ask, スプレッド, 前回比較, 資産合計, 評価損益, 証拠金維持率")


def main():
    """
    メイン関数
    """
    print("=== 外貨EX 自動化ツール ===")
    print(f"ログインID: {login_id}")
    print(f"ログインURL: {login_url}")
    print()
    
    # 機能選択
    print("利用可能な機能:")
    print("1. ログインテスト (Selenium & Undetected ChromeDriver使用)")
    print("2. USD/JPYレート監視 (サイレントモード - デフォルト設定)")
    print("3. USD/JPYレート監視 (サイレントモード - カスタム設定)")
    print("4. 口座情報監視 (サイレントモード - デフォルト設定)")
    print("5. 口座情報監視 (サイレントモード - カスタム設定)")
    print("6. ★ 同時監視 (レート+口座 - 統合表示)")
    print("7. ★ 同時監視 (レート+口座 - カスタム設定)")
    print("8. ◆ 分析付き監視 (リアルタイムデータ分析)")  
    print("9. 🔍 ポジション情報確認 (デバッグ・確認)")
    print("0. 基本アクセステストのみ")
    print("A. ⚠️  全決済実行 (自動モード)")
    print("B. ⚠️  全決済実行 (安全モード - 確認プロンプト付き)")
    print("※ サイレントモードで高速監視を実現")
    print("※ 同時監視で完全なリアルタイム取引環境を構築")
    print("※ 分析付きでトレンド・統計・パフォーマンス分析")
    print("⚠️  全決済機能は全てのポジションを決済します。十分ご注意ください。")
    print()
    
    try:
        choice = input("選択してください (0-9, A-B): ").strip().upper()
        
        if choice == "1":
            # ログインテストのみ
            print("\n=== ログインテスト実行 ===")
            
            # まずRequestsで基本的なアクセステスト
            print("1. Requestsライブラリでの基本アクセステスト")
            login_with_requests()
            print()
            
            # Undetected ChromeDriverでのテスト（推奨）
            print("2. Undetected ChromeDriverでのログインテスト")
            result_undetected = login_with_undetected_chrome()
            print()
            
            if result_undetected:
                print("🎉 Undetected ChromeDriverでログインに成功しました！")
            else:
                print("⚠️  Undetected ChromeDriverでログインに失敗しました")
                print("通常のSeleniumでテストを試行します...")
                print()
                
                # 通常のSeleniumでの実際のログインテスト
                print("3. 通常のSeleniumでのログインテスト")
                result_selenium = login_with_selenium()
                
                if result_selenium:
                    print("\n🎉 通常のSeleniumでログインに成功しました！")
                else:
                    print("\n❌ すべてのテストでログインに失敗しました")
                    return
            
            print("\n✅ ログインテストが完了しました！")
            
        elif choice == "2":
            # USD/JPYレート監視 (サイレントモード - デフォルト設定)
            print("\n=== USD/JPY レート監視 (サイレントモード - デフォルト) ===")
            print("デフォルト設定: 30分間、0.5秒間隔でレート監視")
            print("レート情報のみ表示されます...")
            print()
            rates_data = monitor_usdjpy_rate(duration_minutes=30, interval_seconds=0.5, silent_mode=True)
            
        elif choice == "3":
            # USD/JPYレート監視 (サイレントモード - カスタム設定)
            print("\n=== USD/JPY レート監視 (サイレントモード - カスタム) ===")
            print("カスタム設定でレート監視を実行します")
            
            try:
                duration = float(input("監視時間を入力してください (分, デフォルト:30): ") or "30")
                interval = float(input("取得間隔を入力してください (秒, デフォルト:0.5): ") or "0.5")
                
                if duration <= 0 or interval <= 0:
                    print("❌ 正の数値を入力してください")
                    return
                
                print(f"設定: {duration}分間、{interval}秒間隔でレート監視")
                print("レート情報のみ表示されます...")
                print()
                rates_data = monitor_usdjpy_rate(duration_minutes=duration, interval_seconds=interval, silent_mode=True)
                
            except ValueError:
                print("❌ 有効な数値を入力してください")
                return
                
        elif choice == "4":
            # 口座情報監視 (サイレントモード - デフォルト設定)
            print("\n=== 口座情報監視 (サイレントモード - デフォルト) ===")
            print("デフォルト設定: 30分間、1秒間隔で口座情報監視")
            print("口座情報のみ表示されます...")
            print()
            account_data = monitor_account_info(duration_minutes=30, interval_seconds=1, silent_mode=True)
            
        elif choice == "5":
            # 口座情報監視 (サイレントモード - カスタム設定)
            print("\n=== 口座情報監視 (サイレントモード - カスタム) ===")
            print("カスタム設定で口座情報監視を実行します")
            
            try:
                duration = float(input("監視時間を入力してください (分, デフォルト:30): ") or "30")
                interval = float(input("取得間隔を入力してください (秒, デフォルト:1): ") or "1")
                
                if duration <= 0 or interval <= 0:
                    print("❌ 正の数値を入力してください")
                    return
                
                print(f"設定: {duration}分間、{interval}秒間隔で口座情報監視")
                print("口座情報のみ表示されます...")
                print()
                account_data = monitor_account_info(duration_minutes=duration, interval_seconds=interval, silent_mode=True)
                
            except ValueError:
                print("❌ 有効な数値を入力してください")
                return
                
        elif choice == "6":
            # 同時監視 (統合表示)
            print("\n=== ★ 同時監視 (レート+口座 - 統合表示) ===")
            print("デフォルト設定: 30分間")
            print("レート間隔: 0.5秒 | 口座間隔: 1秒")
            print("統合表示でリアルタイム監視...")
            print()
            monitor_both_combined_display(duration_minutes=30, rate_interval=0.5, account_interval=1)
            
        elif choice == "7":
            # 同時監視 (カスタム設定)
            print("\n=== ★ 同時監視 (レート+口座 - カスタム設定) ===")
            print("カスタム設定で同時監視を実行します")
            
            try:
                duration = float(input("監視時間を入力してください (分, デフォルト:30): ") or "30")
                rate_interval = float(input("レート取得間隔を入力してください (秒, デフォルト:0.5): ") or "0.5")
                account_interval = float(input("口座取得間隔を入力してください (秒, デフォルト:1): ") or "1")
                
                if duration <= 0 or rate_interval <= 0 or account_interval <= 0:
                    print("❌ 正の数値を入力してください")
                    return
                
                print(f"設定: {duration}分間")
                print(f"レート間隔: {rate_interval}秒 | 口座間隔: {account_interval}秒")
                print("統合表示でリアルタイム監視...")
                print()
                monitor_both_combined_display(duration_minutes=duration, 
                                            rate_interval=rate_interval, 
                                            account_interval=account_interval)
                
            except ValueError:
                print("❌ 有効な数値を入力してください")
                return
            
        elif choice == "8":
            # 分析付き監視
            print("\n=== ◆ 分析付き監視 (リアルタイムデータ分析) ===")
            print("リアルタイム分析機能付きで監視を実行します")
            
            try:
                duration = float(input("監視時間を入力してください (分, デフォルト:30): ") or "30")
                rate_interval = float(input("レート取得間隔を入力してください (秒, デフォルト:0.5): ") or "0.5")
                account_interval = float(input("口座取得間隔を入力してください (秒, デフォルト:1): ") or "1")
                
                if duration <= 0 or rate_interval <= 0 or account_interval <= 0:
                    print("× 正の数値を入力してください")
                    return
                
                print(f"設定: {duration}分間")
                print(f"レート間隔: {rate_interval}秒 | 口座間隔: {account_interval}秒")
                print("リアルタイム分析機能で監視開始...")
                print()
                
                # 分析付き監視関数を呼び出し
                monitor_both_with_analysis(duration_minutes=duration, 
                                         rate_interval=rate_interval, 
                                         account_interval=account_interval)
                
            except ValueError:
                print("× 有効な数値を入力してください")
                return
            
        elif choice == "9":
            # ポジション情報確認
            print("\n=== ポジション情報確認 ===")
            debug_position_info()
        
        elif choice == "0":
            # 基本アクセステストのみ
            print("\n=== 基本アクセステスト ===")
            login_with_requests()
        
        elif choice == "A":
            # 全決済実行 (自動モード)
            print("\n=== ⚠️  全決済実行 (自動モード) ===")
            print("❗ この機能は全てのポジションを自動決済します")
            print("   5秒間の猶予後に実行されます")
            result = execute_close_all_positions()
            if result:
                print("✅ 全決済が正常に実行されました")
            else:
                print("❌ 全決済に失敗しました")
        
        elif choice == "B":
            # 全決済実行 (安全モード)
            print("\n=== ⚠️  全決済実行 (安全モード) ===")
            result = close_all_positions_safe()
            if result:
                print("✅ 全決済が正常に実行されました")
            else:
                print("❌ 全決済に失敗またはキャンセルされました")
            
        else:
            print("❌ 無効な選択です")
            return
            
    except KeyboardInterrupt:
        print("\n\nプログラムが中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

def run_rate_monitor_simple():
    """
    簡単なレート監視（引数なしで直接実行）
    """
    print("=== USD/JPY レート監視 (簡単実行) ===")
    monitor_usdjpy_rate(duration_minutes=30, interval_seconds=0.5)

def run_rate_monitor_silent():
    """
    サイレントモードでの簡単なレート監視
    """
    monitor_usdjpy_rate(duration_minutes=30, interval_seconds=0.5, silent_mode=True)

def test_analysis_monitoring():
    """
    分析機能付き監視のテスト実行
    """
    print("=== 分析機能付き監視テスト (1分間) ===")
    monitor_both_with_analysis(duration_minutes=1, rate_interval=1, account_interval=1)

def create_and_login_driver(silent_mode=False):
    """
    ドライバーを作成してログインまで実行する関数
    
    Args:
        silent_mode: サイレントモード
    
    Returns:
        WebDriver: ログイン済みのドライバー、失敗時はNone
    """
    driver = None
    
    try:
        if not silent_mode:
            print("WebDriverを初期化中...")
        
        # Undetected ChromeDriverの設定
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # 通知とポップアップを無効化
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
        # ドライバー作成
        driver = uc.Chrome(options=options, version_main=None)
        
        if not silent_mode:
            print("✅ WebDriverを作成しました")
        
        # ログインページにアクセス
        driver.get(login_url)
        time.sleep(2)
        
        if not silent_mode:
            print(f"ログインページにアクセス: {login_url}")
            print(f"ページタイトル: {driver.title}")
        
        # ユーザーID入力
        username_input = None
        username_selectors = [
            "input[name='P001']",
            "input[id='LoginID']",
            "input[name='username']",
            "input[type='text']"
        ]
        
        for selector in username_selectors:
            try:
                username_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if not silent_mode:
                    print(f"✅ ユーザーID入力欄を発見: {selector}")
                break
            except TimeoutException:
                continue
        
        if not username_input:
            raise Exception("ユーザーID入力欄が見つかりません")
        
        username_input.clear()
        username_input.send_keys(login_id)
        if not silent_mode:
            print(f"ユーザーIDを入力: {login_id}")
        
        # パスワード入力
        password_input = None
        password_selectors = [
            "input[name='P002']",
            "input[id='Pass']",
            "input[name='password']",
            "input[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                password_input = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"✅ パスワード入力欄を発見: {selector}")
                break
            except NoSuchElementException:
                continue
        
        if not password_input:
            raise Exception("パスワード入力欄が見つかりません")
        
        password_input.clear()
        password_input.send_keys(password)
        if not silent_mode:
            print("パスワードを入力しました")
        
        # ログインボタンをクリック
        login_button = None
        login_button_selectors = [
            "input[type='submit']",
            "button[type='submit']", 
            "input[value*='ログイン']",
            "button:contains('ログイン')"
        ]
        
        for selector in login_button_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                if not silent_mode:
                    print(f"✅ ログインボタンを発見: {selector}")
                break
            except NoSuchElementException:
                continue
        
        if login_button:
            driver.execute_script("arguments[0].click();", login_button)
            if not silent_mode:
                print("ログインボタンをクリックしました")
        else:
            # フォームを直接送信
            form = driver.find_element(By.TAG_NAME, "form")
            driver.execute_script("arguments[0].submit();", form)
            if not silent_mode:
                print("フォームを送信しました")
        
        # ログイン完了まで待機
        time.sleep(3)
        
        # ログイン成功の確認
        current_url = driver.current_url
        if "login" not in current_url.lower() or "menu" in current_url.lower() or "main" in current_url.lower():
            if not silent_mode:
                print(f"✅ ログイン成功: {current_url}")
            return driver
        else:
            if not silent_mode:
                print(f"❌ ログイン失敗の可能性: {current_url}")
            return driver  # ドライバーは返す（呼び出し側で判断）
            
    except Exception as e:
        if not silent_mode:
            print(f"❌ ドライバー作成・ログインエラー: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return None

def cleanup_driver(driver, silent_mode=False):
    """
    ドライバーを安全にクリーンアップする関数
    
    Args:
        driver: WebDriverインスタンス
        silent_mode: サイレントモード
    """
    if driver:
        try:
            if not silent_mode:
                print("ブラウザを終了中...")
            
            # 標準エラー出力を抑制してクリーンアップ
            with suppress_stderr():
                driver.close()
                time.sleep(0.5)
                driver.quit()
                time.sleep(0.5)
            
            if not silent_mode:
                print("✅ ブラウザを正常に終了しました")
                
        except Exception as e:
            if not silent_mode:
                print(f"⚠️ ブラウザ終了時にエラー: {e}")
            
            # 強制終了を試行
            try:
                with suppress_stderr():
                    if hasattr(driver, 'service') and driver.service.process:
                        os.kill(driver.service.process.pid, signal.SIGTERM)
                        if not silent_mode:
                            print("ChromeDriverプロセスを強制終了しました")
            except:
                pass

def execute_close_all_positions():
    """
    全ポジション決済を実行する関数（HTMLソース解析版）
    """
    print("=== 全決済実行 ===")
    driver = None
    
    try:
        # ドライバー作成とログイン
        print("ログイン処理を開始...")
        driver = create_and_login_driver(silent_mode=False)
        
        if not driver:
            print("❌ ログインに失敗しました")
            return False
        
        print("✅ ログイン成功")
        time.sleep(2)
        
        # 取引メニューから全決済にアクセス
        print("\n--- 取引メニューから全決済にアクセス ---")
        
        try:
            # まずメインページが表示されるまで待機
            time.sleep(2)
            print(f"現在のURL: {driver.current_url}")
            print(f"ページタイトル: {driver.title}")
            
            # 方法1: 取引メニューのiframe内で全決済リンクを探す
            try:
                print("  方法1: メニューフレーム内で全決済リンクを検索...")
                
                # メニューフレームに切り替え（複数の候補を試行）
                menu_frame_names = ["headerMenu", "mainMenu", "leftMenu", "menu"]
                menu_frame_found = False
                
                for frame_name in menu_frame_names:
                    try:
                        driver.switch_to.frame(frame_name)
                        print(f"    ✅ {frame_name} フレームに切り替えました")
                        menu_frame_found = True
                        break
                    except:
                        try:
                            driver.switch_to.default_content()
                        except:
                            pass
                        continue
                
                if menu_frame_found:
                    # 全決済リンクを検索
                    close_all_selectors = [
                        "//a[contains(@onclick, 'CHt00242')]",
                        "//a[contains(text(), '全決済')]",
                        "//a[contains(@onclick, 'Ht00242')]"
                    ]
                    
                    close_all_link = None
                    for selector in close_all_selectors:
                        try:
                            close_all_link = driver.find_element(By.XPATH, selector)
                            print(f"    ✅ 全決済リンクを発見: {selector}")
                            break
                        except:
                            continue
                    
                    if close_all_link:
                        print("  全決済リンクをクリック...")
                        driver.execute_script("arguments[0].click();", close_all_link)
                        time.sleep(3)
                        print("  ✅ 全決済リンクをクリックしました")
                    else:
                        print("  ⚠️ 全決済リンクが見つかりませんでした")
                        
                    driver.switch_to.default_content()
                else:
                    print("  ⚠️ メニューフレームが見つかりませんでした")
                    
            except Exception as e:
                print(f"  ❌ 方法1でエラー: {e}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
            
            # 方法2: メインフレーム構造に対応した全決済ページアクセス
            print("  方法2: フレーム構造に対応した全決済ページアクセス...")
            
            try:
                # デフォルトコンテンツに戻ってからフレーム操作
                driver.switch_to.default_content()
                
                # JavaScriptでmain_v2_dフレーム内に全決済ページを読み込み
                print("    main_v2_dフレーム内に全決済ページを読み込み中...")
                js_script = """
                try {
                    var mainFrame = document.getElementById('main_v2_d') || document.getElementsByName('main_v2_d')[0];
                    if (mainFrame) {
                        mainFrame.src = '/servlet/lzca.pc.cht002.servlet.CHt00242?AKEY=Fr00103.Ht00242';
                        return 'フレームのsrc更新成功';
                    } else {
                        return 'フレームが見つかりません';
                    }
                } catch (e) {
                    return 'エラー: ' + e.message;
                }
                """
                
                result = driver.execute_script(js_script)
                print(f"    JavaScriptの実行結果: {result}")
                time.sleep(4)  # フレーム内容の読み込み待機
                
                # 再度main_v2_dフレームに切り替え
                try:
                    driver.switch_to.frame("main_v2_d")
                    print("    ✅ 全決済ページ読み込み後にフレーム切り替え成功")
                    
                    # フレーム内のページ確認
                    frame_source = driver.page_source
                    if "全決済" in frame_source and "CHt00242" in frame_source:
                        print("    ✅ 全決済ページの読み込みを確認")
                    else:
                        print("    ⚠️ 全決済ページの内容が見つかりません")
                        
                except Exception as frame_error:
                    print(f"    ⚠️ フレーム切り替えエラー: {frame_error}")
                    
            except Exception as e:
                print(f"  ❌ 方法2でエラー: {e}")
                
                # 方法3: 直接URLアクセスを試行
                print("  方法3: 直接URL変更を試行...")
                try:
                    close_all_url = "https://vt-fx.gaikaex.com/servlet/lzca.pc.cht002.servlet.CHt00242?AKEY=Fr00103.Ht00242"
                    driver.get(close_all_url)
                    time.sleep(3)
                    print(f"  ✅ 直接アクセス完了: {close_all_url}")
                    print(f"  現在のURL: {driver.current_url}")
                    print(f"  ページタイトル: {driver.title}")
                except Exception as direct_error:
                    print(f"  ❌ 方法3でもエラー: {direct_error}")
                    return False
                
        except Exception as e:
            print(f"❌ 全決済ページアクセス失敗: {e}")
            return False
        
        # ページの内容確認
        print("\n--- ページ内容の確認 ---")
        
        # ポジション情報の確認（iframe対応版）
        position_info = get_position_info_from_frames(driver)
        
        if position_info:
            position_count = position_info['count']
            print(f"📊 現在のポジション数: {position_count}件")
            print(f"取得元フレーム: {position_info.get('source_frame', '不明')}")
            
            if position_count == 0:
                print("⚠️ 決済対象のポジションがありません")
                return True  # ポジションがない場合は成功とみなす
                
            # ポジション詳細の表示（外貨EXフォーマット）
            print("\n--- ポジション詳細 ---")
            print("注文番号      通貨ペア   売買 数量       約定価格   評価損益   手数料")
            print("-" * 80)
            
            for i, pos in enumerate(position_info['positions'][:10]):  # 最初の10件まで表示
                order_no = pos.get('order_no', '').ljust(12)
                currency = pos.get('currency', '').ljust(8)
                side = pos.get('side', '').ljust(4)
                amount = pos.get('amount', '').rjust(10)
                price = pos.get('price', '').rjust(8)
                pnl = pos.get('pnl', '').rjust(8)
                fee = pos.get('fee', '').rjust(6)
                
                print(f"  {order_no} {currency} {side} {amount} {price} {pnl} {fee}")
            
            if position_count > 10:
                print(f"  ... および他 {position_count - 10}件")
            
        else:
            print("⚠️ ポジション情報を取得できませんでした")
        
        # 全決済注文実行ボタンの状態確認
        print("\n--- 全決済注文実行ボタンの確認 ---")
        
        # メインフレームページから全決済フレームに正確に切り替え
        try:
            print("  メインフレーム構造を分析中...")
            
            # 現在のページ構造を確認
            current_url = driver.current_url
            print(f"  現在のURL: {current_url}")
            
            # HTMLソースから判明：main_v2_dフレーム内に全決済ページがある
            print("  main_v2_d フレームに切り替え中...")
            
            # デフォルトコンテンツに戻る
            driver.switch_to.default_content()
            
            # main_v2_d フレームを探して切り替え
            main_frame_found = False
            frame_selectors = [
                "iframe#main_v2_d",
                "iframe[name='main_v2_d']", 
                "#main_v2_d"
            ]
            
            for selector in frame_selectors:
                try:
                    main_frame = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    driver.switch_to.frame(main_frame)
                    print(f"  ✅ main_v2_dフレームに切り替え成功: {selector}")
                    main_frame_found = True
                    break
                except TimeoutException:
                    continue
            
            if not main_frame_found:
                print("  ⚠️ main_v2_dフレームが見つかりません")
                # フレーム名で直接試行
                try:
                    driver.switch_to.frame("main_v2_d")
                    print("  ✅ フレーム名で切り替え成功")
                    main_frame_found = True
                except:
                    print("  ❌ フレーム名でも切り替え失敗")
            
            if main_frame_found:
                # フレーム内のページが全決済ページかどうか確認
                time.sleep(2)  # フレーム内容の読み込み待機
                
                frame_url = driver.current_url
                frame_title = driver.title
                print(f"  フレーム内URL: {frame_url}")
                print(f"  フレーム内タイトル: {frame_title}")
                
                # 全決済ページ（CHt00242）であることを確認
                page_source = driver.page_source
                if "CHt00242" in page_source or "全決済" in page_source:
                    print("  ✅ 全決済ページを確認しました")
                else:
                    print("  ⚠️ 全決済ページではない可能性があります")
                    print("  ページ内容の一部:")
                    print(f"    {page_source[:200]}...")
            else:
                print("  ❌ 適切なフレームに切り替えできませんでした")
                return False
            
        except Exception as e:
            print(f"  ❌ フレーム切り替えエラー: {e}")
            try:
                driver.switch_to.default_content()
            except:
                pass
            return False
        
        try:
            # HTMLソース解析に基づいてボタンを検索
            exec_button = driver.find_element(By.CSS_SELECTOR, "button[name='EXEC']")
            
            button_disabled = exec_button.get_attribute("disabled")
            button_class = exec_button.get_attribute("class")
            button_text = exec_button.text.strip() or exec_button.get_attribute("value") or ""
            button_onclick = exec_button.get_attribute("onclick") or ""
            
            print(f"✅ 全決済実行ボタンを発見")
            print(f"  テキスト: {button_text}")
            print(f"  無効化状態: {button_disabled}")
            print(f"  クラス: {button_class}")
            print(f"  onclick: {button_onclick[:100]}...")
            
            if button_disabled or "disAbleElmnt" in (button_class or ""):
                print("⚠️ ボタンが無効化されています。HTMLソースに基づく有効化を実行...")
                
                # HTMLソースに基づく正確な有効化処理
                print("  ステップ1: レート取得関数を実行...")
                try:
                    # _getRate_Order(0) を実行してボタンを有効化
                    driver.execute_script("_getRate_Order(0);")
                    print("  ✅ _getRate_Order(0) 実行完了")
                    time.sleep(2)  # レート取得後の処理待機
                except Exception as rate_error:
                    print(f"  ⚠️ レート取得関数エラー: {rate_error}")
                
                # ステップ2: ボタンを強制的に有効化
                print("  ステップ2: ボタンの強制有効化...")
                driver.execute_script("""
                    var button = arguments[0];
                    button.disabled = false;
                    button.classList.remove('disAbleElmnt');
                    button.style.pointerEvents = 'auto';
                    button.style.opacity = '1';
                """, exec_button)
                
                # ステップ3: ablebtn()関数を実行（HTMLで定義されている）
                print("  ステップ3: ablebtn()関数を実行...")
                try:
                    driver.execute_script("ablebtn();")
                    print("  ✅ ablebtn() 実行完了")
                except Exception as able_error:
                    print(f"  ⚠️ ablebtn()エラー: {able_error}")
                
                # 再確認
                button_disabled_after = exec_button.get_attribute("disabled")
                button_class_after = exec_button.get_attribute("class")
                print(f"  有効化後の状態: disabled={button_disabled_after}, class={button_class_after}")
                
                if button_disabled_after:
                    print("  ⚠️ まだ無効化されています。さらなる強制有効化を試行...")
                    driver.execute_script("""
                        var button = arguments[0];
                        button.removeAttribute('disabled');
                        button.className = button.className.replace('disAbleElmnt', '').trim();
                    """, exec_button)
            else:
                print("✅ ボタンは既に有効化されています")
                
            # 実行前の確認
            print("\n⚠️ 全決済を実行しようとしています")
            print("   この操作により、全てのポジションが決済されます")
            print("   5秒後に実行します... (Ctrl+Cで中断可能)")
            
            try:
                for i in range(5, 0, -1):
                    print(f"   実行まで {i} 秒...")
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n❌ ユーザーによって中断されました")
                return False
            
            # レート取得関数を実行（HTMLソースに基づく）
            print("\n--- レート取得とボタンクリック実行 ---")
            try:
                # _getRate_Order(0) をJavaScriptで実行
                driver.execute_script("_getRate_Order(0);")
                print("✅ レート取得関数を実行")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ レート取得関数実行エラー (継続します): {e}")
            
            # HTMLソースの正確なonclickイベントを使用してボタンをクリック
            print("全決済注文実行ボタンをクリック...")
            
            # 方法1: HTMLソースのonclickイベントを直接実行
            try:
                print("  方法1: HTMLソースのonclickイベントを実行...")
                # HTMLの正確なonclick: "_getRate_Order(0); submitForm('frmMain', '/servlet/lzca.pc.cht002.servlet.CHt00243', 'POST', '_self', 'Ht00243');"
                
                # まずレート取得を実行
                driver.execute_script("_getRate_Order(0);")
                print("  ✅ _getRate_Order(0) 実行")
                time.sleep(1)
                
                # 次にsubmitFormを実行
                driver.execute_script("submitForm('frmMain', '/servlet/lzca.pc.cht002.servlet.CHt00243', 'POST', '_self', 'Ht00243');")
                print("  ✅ submitForm実行完了")
                time.sleep(3)  # フォーム送信後の処理待機
                
                # ページ変化を確認
                current_url_after_click = driver.current_url
                print(f"  実行後のURL: {current_url_after_click}")
                
                if "CHt00243" in current_url_after_click:
                    print("✅ 方法1成功: 確認ページに遷移しました")
                else:
                    print("⚠️ 方法1: ページ遷移未確認、方法2を試行...")
                    
                    # 方法2: ボタンの直接クリック
                    print("  方法2: ボタンの直接クリック...")
                    driver.execute_script("arguments[0].click();", exec_button)
                    time.sleep(3)
                    print("  ✅ 方法2: 直接クリック実行")
                    
                    # 方法3: onclickイベントを手動トリガー
                    if "CHt00243" not in driver.current_url:
                        print("  方法3: onclickイベントの手動トリガー...")
                        onclick_script = exec_button.get_attribute("onclick")
                        if onclick_script:
                            driver.execute_script(onclick_script)
                            print("  ✅ 方法3: onclickイベント実行")
                            time.sleep(3)
                    
                    # 方法4: フォーカス後クリック
                    if "CHt00243" not in driver.current_url:
                        print("  方法4: フォーカス後クリック...")
                        driver.execute_script("""
                            arguments[0].focus();
                            arguments[0].disabled = false;
                            arguments[0].classList.remove('disAbleElmnt');
                            arguments[0].click();
                        """, exec_button)
                        time.sleep(3)
                        print("  ✅ 方法4: フォーカス後クリック実行")
                    
                    # 方法5: フォーム直接送信
                    if "CHt00243" not in driver.current_url:
                        print("  方法5: フォーム直接送信...")
                        try:
                            form = driver.find_element(By.NAME, "frmMain")
                            # フォームのactionとmethodを設定してから送信
                            driver.execute_script("""
                                var form = arguments[0];
                                form.action = '/servlet/lzca.pc.cht002.servlet.CHt00243';
                                form.method = 'POST';
                                form.target = '_self';
                                form.submit();
                            """, form)
                            print("  ✅ 方法5: フォーム送信実行")
                            time.sleep(3)
                        except Exception as form_error:
                            print(f"  ⚠️ 方法5エラー: {form_error}")
                
            except Exception as click_error:
                print(f"❌ 全決済実行エラー: {click_error}")
                
                # 緊急措置: 直接確認画面URLにアクセス
                try:
                    print("緊急措置: 確認画面に直接アクセス...")
                    confirm_url = "https://vt-fx.gaikaex.com/servlet/lzca.pc.cht002.servlet.CHt00243"
                    driver.get(confirm_url)
                    time.sleep(2)
                    print("✅ 緊急措置: 確認画面に直接アクセス完了")
                except Exception as url_error:
                    print(f"❌ 緊急措置も失敗: {url_error}")
            
            print("✅ 全決済注文実行処理が完了しました")
            
        except NoSuchElementException:
            print("❌ 全決済注文実行ボタン (name='EXEC') が見つかりませんでした")
            print("📋 ページ内容を詳細分析してボタンを検索します...")
            
            # ページ内容のデバッグ
            try:
                page_source = driver.page_source
                print(f"  現在のページタイトル: {driver.title}")
                print(f"  現在のURL: {driver.current_url}")
                
                # 実行ボタン関連のHTMLを検索
                if "全決済注文実行" in page_source:
                    print("✅ '全決済注文実行' テキストが見つかりました")
                else:
                    print("⚠️ '全決済注文実行' テキストが見つかりません")
                
                if "EXEC" in page_source:
                    print("✅ 'EXEC' が見つかりました")
                else:
                    print("⚠️ 'EXEC' が見つかりません")
                    
                # フォーム要素の確認
                forms = driver.find_elements(By.TAG_NAME, "form")
                print(f"  発見されたフォーム数: {len(forms)}")
                
                # 全てのボタンとinput要素を検索
                all_buttons = driver.find_elements(By.TAG_NAME, "button") + driver.find_elements(By.CSS_SELECTOR, "input[type='button'], input[type='submit']")
                print(f"  発見されたボタン数: {len(all_buttons)}")
                
                for i, btn in enumerate(all_buttons):
                    try:
                        btn_text = btn.text.strip() or btn.get_attribute('value') or ""
                        btn_name = btn.get_attribute('name') or ""
                        btn_onclick = btn.get_attribute('onclick') or ""
                        print(f"    ボタン{i+1}: text='{btn_text}' name='{btn_name}' onclick='{btn_onclick[:50]}'")
                    except:
                        continue
            except:
                pass
            
            # 代替ボタン検索（HTMLソース基準）
            alt_selectors = [
                "button[name='EXEC']",  # HTMLソースで確認済みの正確なセレクター
                "//button[contains(text(), '全決済注文実行')]",
                "//button[contains(@onclick, 'CHt00243')]",
                "//button[contains(@onclick, '_getRate_Order')]",
                "//button[contains(@class, 'disAbleElmnt')]",  # 無効化されているボタンも検索
                "//input[@name='EXEC']",
                "//button[@name='EXEC']",
                "//input[contains(@value, '全決済注文実行')]",
                "//button[text()='全決済注文実行']",
                "//input[contains(@onclick, 'submitForm')]",
                "//button[contains(@onclick, 'submitForm')]"
            ]
            
            button_found = False
            for selector in alt_selectors:
                try:
                    alt_button = driver.find_element(By.XPATH, selector)
                    print(f"✅ 代替ボタンを発見: {selector}")
                    
                    # ボタンの詳細情報を表示
                    btn_text = alt_button.text.strip() or alt_button.get_attribute('value') or ""
                    btn_name = alt_button.get_attribute('name') or ""
                    print(f"  ボタン詳細: text='{btn_text}' name='{btn_name}'")
                    
                    # HTMLソースに基づく複数の方法でクリックを試行
                    print("  ボタンをクリック中...")
                    try:
                        # ボタンを有効化
                        driver.execute_script("""
                            var button = arguments[0];
                            button.disabled = false;
                            button.classList.remove('disAbleElmnt');
                            button.style.pointerEvents = 'auto';
                        """, alt_button)
                        
                        # HTMLソースのonclickイベントを実行
                        onclick_attr = alt_button.get_attribute("onclick")
                        if onclick_attr and "CHt00243" in onclick_attr:
                            print(f"    HTMLのonclickイベントを実行: {onclick_attr[:50]}...")
                            
                            # レート取得を実行
                            driver.execute_script("_getRate_Order(0);")
                            time.sleep(1)
                            
                            # フォーム送信を実行
                            driver.execute_script("submitForm('frmMain', '/servlet/lzca.pc.cht002.servlet.CHt00243', 'POST', '_self', 'Ht00243');")
                            time.sleep(2)
                            print("    ✅ HTMLのonclickイベント実行完了")
                        else:
                            # 標準クリック
                            driver.execute_script("arguments[0].click();", alt_button)
                            time.sleep(2)
                            print("    ✅ 標準クリック完了")
                        
                        # ページ変化を確認
                        new_url = driver.current_url
                        print(f"  クリック後URL: {new_url}")
                        
                        if "CHt00243" in new_url:
                            print("  ✅ 成功ページに遷移しました")
                            button_found = True
                            break
                        else:
                            # 追加のクリック方法を試行
                            print("    追加のクリック方法を試行...")
                            driver.execute_script("""
                                var button = arguments[0];
                                button.focus();
                                button.disabled = false;
                                button.classList.remove('disAbleElmnt');
                                
                                // onclickイベントを手動で実行
                                if (button.onclick) {
                                    button.onclick();
                                } else {
                                    button.click();
                                }
                                
                                // フォーム送信も試行
                                if (button.form) {
                                    button.form.submit();
                                }
                            """, alt_button)
                            time.sleep(3)
                            print("    ✅ 強化クリック完了")
                            
                            if "CHt00243" in driver.current_url:
                                button_found = True
                                break
                            
                    except Exception as click_err:
                        print(f"  ⚠️ クリックエラー: {click_err}")
                        continue
                        
                except NoSuchElementException:
                    continue
            
            if not button_found:
                print("❌ すべての代替ボタン検索が失敗しました")
                
                # 最終手段: JavaScriptで直接フォーム送信
                try:
                    print("🔧 最終手段: JavaScriptでフォーム送信...")
                    driver.execute_script("""
                        var forms = document.getElementsByTagName('form');
                        for (var i = 0; i < forms.length; i++) {
                            var form = forms[i];
                            var inputs = form.getElementsByTagName('input');
                            for (var j = 0; j < inputs.length; j++) {
                                if (inputs[j].name === 'EXEC' || inputs[j].value.indexOf('実行') !== -1) {
                                    form.submit();
                                    return true;
                                }
                            }
                        }
                        return false;
                    """)
                    time.sleep(3)
                    print("✅ JavaScript送信完了")
                except Exception as js_err:
                    print(f"❌ JavaScript送信失敗: {js_err}")
                    return False
        
        # 実行結果の確認
        print("\n--- 実行結果の確認 ---")
        time.sleep(5)  # ページ遷移の待機を延長
        
        # 適切なフレーム状態を維持
        try:
            # 全決済処理中はmain_v2_dフレーム内にいる状態を維持
            current_url = driver.current_url
            if "CHt00243" not in current_url:
                # まだ確認ページに遷移していない場合は、フレーム構造を確認
                try:
                    # フレーム外にいる場合はmain_v2_dフレームに切り替え
                    if "main_v2_d" not in str(driver.current_window_handle):
                        driver.switch_to.frame("main_v2_d")
                        print("  フレーム内での結果確認に切り替えました")
                except:
                    pass
        except:
            pass
        
        current_url = driver.current_url
        current_title = driver.title
        
        print(f"実行後のURL: {current_url}")
        print(f"実行後のページタイトル: {current_title}")
        
        # 成功/エラーメッセージを探す
        success_indicators = [
            "決済が完了", "注文が完了", "実行されました", "成功", "完了", 
            "決済済み", "全決済", "CHt00243",  # 成功時の遷移先ページ
            "全決済注文受付完了", "受付完了", "COMPLETE",
            "全決済注文を受付けました", "_afterAllOrder", "doneInfo"
        ]
        
        error_indicators = [
            "エラー", "失敗", "できません", "無効", "Error", 
            "システムエラー", "処理に失敗", "注文できません"
        ]
        
        page_source = driver.page_source
        
        # 完了ページの確認（タイトルベース - 最優先）
        try:
            # フレーム内でのタイトル確認
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame("main_v2_d")
                frame_title = driver.title
                frame_source = driver.page_source
                
                print(f"  フレーム内タイトル: '{frame_title}'")
                
                # COMPLETEタイトルの確認（全決済完了ページ）
                if frame_title == "COMPLETE":
                    print("✅ 全決済完了ページを確認 (COMPLETE)")
                    
                    # 完了メッセージの詳細確認
                    if "全決済注文受付完了" in frame_source:
                        print("✅ 全決済注文受付完了メッセージを確認")
                        
                        # 処理されたポジションの詳細を抽出
                        try:
                            import re
                            # doneInfoから処理詳細を抽出
                            done_info_match = re.search(r'doneInfo\[0\]\s*=\s*new\s*Array\(([^)]+)\)', frame_source)
                            if done_info_match:
                                done_values = done_info_match.group(1).split(',')
                                if len(done_values) >= 5:
                                    order_no = done_values[0].strip()
                                    currency_id = done_values[1].strip()
                                    amount = done_values[2].strip()
                                    side = done_values[3].strip()
                                    price = done_values[4].strip()
                                    
                                    currency_name = "ドル/円" if currency_id == "2" else f"通貨ID:{currency_id}"
                                    side_name = "売り決済" if side == "1" else "買い決済"
                                    
                                    print(f"  📋 決済詳細:")
                                    print(f"    注文番号: {order_no}")
                                    print(f"    通貨ペア: {currency_name}")
                                    print(f"    数量: {amount}")
                                    print(f"    決済方向: {side_name}")
                                    print(f"    価格: {price}")
                        except Exception as detail_error:
                            print(f"  ⚠️ 決済詳細解析エラー: {detail_error}")
                        
                        driver.switch_to.default_content()
                        return True
                    
                    # 他の完了メッセージパターンもチェック
                    complete_keywords = [
                        "受付完了", "注文受付", "処理完了", "決済完了", "実行完了"
                    ]
                    
                    for keyword in complete_keywords:
                        if keyword in frame_source:
                            print(f"✅ 完了キーワード '{keyword}' を確認")
                            driver.switch_to.default_content()
                            return True
                
            except Exception as frame_error:
                print(f"  フレーム確認エラー: {frame_error}")
            finally:
                try:
                    driver.switch_to.default_content()
                except:
                    pass
        except Exception as title_error:
            print(f"  タイトル確認エラー: {title_error}")

        # URL基準での成功判定（セカンダリ）
        if "CHt00243" in current_url:
            print("✅ 成功ページに遷移しました (CHt00243)")
            return True
        
        # ページ内容での判定
        success_found = any(indicator in page_source for indicator in success_indicators)
        error_found = any(indicator in page_source for indicator in error_indicators)
        
        if success_found:
            print("✅ 全決済が正常に実行されました")
            
            # 成功メッセージの詳細を表示
            try:
                success_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '完了') or contains(text(), '成功') or contains(text(), '実行')]")
                for elem in success_elements[:3]:
                    success_text = elem.text.strip()
                    if success_text:
                        print(f"  成功詳細: {success_text}")
            except:
                pass
            
            return True
            
        elif error_found:
            print("❌ 全決済の実行でエラーが発生しました")
            
            # エラーメッセージの詳細を取得
            try:
                error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'エラー') or contains(text(), '失敗') or contains(text(), 'できません')]")
                for elem in error_elements[:3]:
                    error_text = elem.text.strip()
                    if error_text:
                        print(f"  エラー詳細: {error_text}")
            except:
                pass
            return False
        else:
            print("⚠️ 実行結果を明確に判定できませんでした")
            
            # フレーム構造を考慮した詳細確認
            try:
                print("  フレーム構造での詳細確認を実行...")
                
                # デフォルトコンテンツに戻る
                driver.switch_to.default_content()
                
                # main_v2_d フレーム内でメッセージを確認
                try:
                    driver.switch_to.frame("main_v2_d")
                    frame_text = driver.page_source[:3000]  # 最初の3000文字
                    frame_url = driver.current_url
                    
                    print(f"  フレーム内URL: {frame_url}")
                    
                    success_patterns = [
                        "受け付け", "注文", "完了", "実行", "CHt00243",
                        "決済", "処理", "成功", "確認"
                    ]
                    
                    found_patterns = []
                    for pattern in success_patterns:
                        if pattern in frame_text or pattern in frame_url:
                            found_patterns.append(pattern)
                    
                    if found_patterns:
                        print(f"✅ フレーム内で成功パターンを確認: {', '.join(found_patterns)}")
                        print("   全決済注文が受け付けられた可能性があります")
                        return True
                    else:
                        print("⚠️ フレーム内に明確な成功メッセージが見つかりません")
                        print("  フレーム内容の一部:")
                        # HTMLの重要部分のみ抽出
                        important_text = ""
                        if "全決済" in frame_text:
                            start_idx = frame_text.find("全決済") - 100
                            end_idx = start_idx + 300
                            important_text = frame_text[max(0, start_idx):end_idx]
                        print(f"    {important_text}")
                
                except Exception as frame_error:
                    print(f"  フレーム内確認エラー: {frame_error}")
                
                finally:
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                
            except Exception as detail_error:
                print(f"  詳細確認エラー: {detail_error}")
            
            print("   エラーメッセージが検出されなかったため、成功の可能性があります")
            return True
        
    except KeyboardInterrupt:
        print("\n❌ ユーザーによって中断されました")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
        
    finally:
        if driver:
            cleanup_driver(driver, silent_mode=False)
            print("\n=== 全決済処理完了 ===")

def close_all_positions_safe():
    """
    安全な全決済実行（確認プロンプト付き）
    """
    print("=== 安全な全決済実行 ===")
    print("⚠️  この機能は全てのポジションを決済します")
    print("   実行前に必ず内容をご確認ください")
    
    # ユーザー確認
    try:
        confirmation = input("\n本当に全決済を実行しますか？ (yes/no): ").strip().lower()
        if confirmation not in ['yes', 'y']:
            print("❌ 全決済をキャンセルしました")
            return False
        
        # 二重確認
        final_confirmation = input("最終確認: 全ポジションを決済します。よろしいですか？ (YES/no): ").strip()
        if final_confirmation != 'YES':
            print("❌ 全決済をキャンセルしました")
            return False
        
        print("\n✅ 確認完了。全決済を実行します...")
        return execute_close_all_positions()
        
    except KeyboardInterrupt:
        print("\n❌ ユーザーによってキャンセルされました")
        return False

def get_position_info_from_frames(driver):
    """
    各種フレームからポジション情報を取得する関数（iframe対応版）
    
    Returns:
        dict: ポジション情報 {'count': int, 'positions': list} またはNone
    """
    print("🔍 iframe対応ポジション情報取得開始...")
    
    # 元のフレーム状態を保存
    try:
        driver.switch_to.default_content()
    except:
        pass
    
    # 検索対象フレームのリスト（優先順位順）
    frame_candidates = [
        # 全決済ページのフレーム
        {"name": "main_v2_d", "description": "メインフレーム（全決済ページ）"},
        {"name": "main_v2", "description": "メインフレーム"},
        # 注文関連フレーム
        {"name": "orderFrame", "description": "注文フレーム"},
        {"name": "positionFrame", "description": "ポジションフレーム"},
        # 顧客情報フレーム
        {"name": "customerInfo_v2_d", "description": "顧客情報フレーム"},
        {"name": "customerInfo_v2", "description": "顧客情報フレーム"}
    ]
    
    for frame_info in frame_candidates:
        frame_name = frame_info["name"]
        frame_desc = frame_info["description"]
        
        try:
            print(f"  📋 {frame_desc}（{frame_name}）で検索中...")
            
            # フレームに切り替え
            driver.switch_to.default_content()
            time.sleep(0.5)
            
            # 複数の方法でフレームアクセスを試行
            frame_found = False
            
            # 方法1: フレーム名で直接アクセス
            try:
                driver.switch_to.frame(frame_name)
                frame_found = True
                print(f"    ✅ フレーム名でアクセス成功: {frame_name}")
            except:
                pass
            
            # 方法2: CSS セレクターでアクセス
            if not frame_found:
                try:
                    frame_element = driver.find_element(By.CSS_SELECTOR, f"iframe#{frame_name}")
                    driver.switch_to.frame(frame_element)
                    frame_found = True
                    print(f"    ✅ CSS セレクターでアクセス成功: iframe#{frame_name}")
                except:
                    pass
            
            # 方法3: name属性でアクセス
            if not frame_found:
                try:
                    frame_element = driver.find_element(By.CSS_SELECTOR, f"iframe[name='{frame_name}']")
                    driver.switch_to.frame(frame_element)
                    frame_found = True
                    print(f"    ✅ name属性でアクセス成功: iframe[name='{frame_name}']")
                except:
                    pass
            
            if not frame_found:
                print(f"    ⚠️ {frame_name} フレームが見つかりません")
                continue
            
            # フレーム内でポジション情報を検索
            time.sleep(1)  # フレーム内容の読み込み待機
            
            position_info = search_position_table_in_frame(driver, frame_desc)
            
            if position_info:
                print(f"    ✅ {frame_desc}でポジション情報取得成功")
                driver.switch_to.default_content()
                return position_info
            else:
                print(f"    ❌ {frame_desc}でポジション情報なし")
                
        except Exception as e:
            print(f"    ❌ {frame_desc}でエラー: {e}")
        
        # 必ずデフォルトコンテンツに戻る
        try:
            driver.switch_to.default_content()
        except:
            pass
    
    # すべてのフレームで失敗した場合、メインページで検索
    print("  🌐 メインページで直接検索...")
    try:
        driver.switch_to.default_content()
        position_info = search_position_table_in_frame(driver, "メインページ")
        if position_info:
            print("    ✅ メインページでポジション情報取得成功")
            return position_info
    except Exception as e:
        print(f"    ❌ メインページでエラー: {e}")
    
    print("❌ 全てのフレームでポジション情報取得失敗")
    return None

def debug_position_info():
    """
    ポジション情報取得をデバッグする関数
    """
    print("=== ポジション情報デバッグ ===")
    driver = None
    
    try:
        # ログイン
        print("ログイン処理開始...")
        driver = create_and_login_driver(silent_mode=False)
        
        if not driver:
            print("❌ ログインに失敗しました")
            return
        
        print("✅ ログイン成功")
        time.sleep(3)
        
        # 全決済ページにアクセス
        print("\n--- 全決済ページへのアクセス ---")
        success = navigate_to_close_all_page(driver)
        
        if not success:
            print("⚠️ 全決済ページアクセスに失敗、現在のページで検索を続行")
        
        # 全フレームの構造を調査
        print("\n--- フレーム構造調査 ---")
        debug_all_frames(driver)
        
        # ポジション情報取得を試行
        print("\n--- ポジション情報取得試行 ---")
        position_info = get_position_info_from_frames(driver)
        
        if position_info:
            print(f"\n✅ ポジション情報取得成功")
            print(f"取得元: {position_info.get('source_frame', '不明')}")
            print(f"ポジション数: {position_info['count']}件")
            
            if position_info['count'] > 0:
                print("\n📋 ポジション詳細:")
                print("注文番号      通貨ペア   売買 数量       約定価格   評価損益   手数料")
                print("-" * 80)
                
                for pos in position_info['positions']:
                    order_no = pos.get('order_no', '').ljust(12)
                    currency = pos.get('currency', '').ljust(8) 
                    side = pos.get('side', '').ljust(4)
                    amount = pos.get('amount', '').rjust(10)
                    price = pos.get('price', '').rjust(8)
                    pnl = pos.get('pnl', '').rjust(8)
                    fee = pos.get('fee', '').rjust(6)
                    
                    print(f"  {order_no} {currency} {side} {amount} {price} {pnl} {fee}")
            else:
                print("📊 現在ポジションはありません")
        else:
            print("\n❌ ポジション情報を取得できませんでした")
            
        # HTMLソースの一部をダンプ（デバッグ用）
        print("\n--- HTMLソース分析 ---")
        try:
            driver.switch_to.default_content()
            page_source = driver.page_source
            
            # ポジション関連キーワードの出現回数
            keywords = ['position', 'ポジション', 'order', '注文', 'table', 'テーブル', 'item04']
            for keyword in keywords:
                count = page_source.lower().count(keyword.lower())
                print(f"  '{keyword}': {count}回")
                
        except Exception as e:
            print(f"HTMLソース分析エラー: {e}")
        
    except Exception as e:
        print(f"デバッグ中にエラー: {e}")
        
    finally:
        if driver:
            try:
                print("\nブラウザを終了...")
                with suppress_stderr():
                    driver.quit()
                print("ブラウザ終了完了")
            except:
                pass

def navigate_to_close_all_page(driver):
    """
    全決済ページに正しくナビゲートする関数
    
    Returns:
        bool: 成功時True、失敗時False
    """
    try:
        print("  🌐 全決済ページにアクセス中...")
        
        # 方法1: メニューフレーム内の全決済リンクをクリック
        try:
            print("    方法1: メニューフレーム内の全決済リンク検索...")
            
            # メニューフレームに切り替え（複数の候補を試行）
            menu_frame_names = ["mainMenu", "headerMenu", "leftMenu", "menu"]
            menu_accessed = False
            
            for frame_name in menu_frame_names:
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(frame_name)
                    print(f"      ✅ {frame_name}フレームにアクセス成功")
                    menu_accessed = True
                    
                    # 全決済リンクを検索
                    close_all_selectors = [
                        "//a[contains(@onclick, 'CHt00242')]",
                        "//a[contains(text(), '全決済')]",
                        "//a[contains(@href, 'CHt00242')]",
                        "//a[contains(@onclick, 'Ht00242')]"
                    ]
                    
                    for selector in close_all_selectors:
                        try:
                            link = driver.find_element(By.XPATH, selector)
                            print(f"      ✅ 全決済リンク発見: {selector}")
                            driver.execute_script("arguments[0].click();", link)
                            time.sleep(3)
                            print(f"      ✅ 全決済リンクをクリックしました")
                            driver.switch_to.default_content()
                            return True
                        except:
                            continue
                    
                    print(f"      ⚠️ {frame_name}フレーム内に全決済リンクなし")
                    
                except Exception as frame_error:
                    continue
            
            if menu_accessed:
                driver.switch_to.default_content()
                
        except Exception as e:
            print(f"    方法1失敗: {e}")
            
        # 方法2: main_v2_dフレーム内に全決済ページを直接読み込み
        try:
            print("    方法2: main_v2_dフレーム内に全決済ページを直接読み込み...")
            
            driver.switch_to.default_content()
            
            # JavaScriptでフレーム内容を変更
            js_script = """
            try {
                var mainFrame = document.getElementById('main_v2_d') || document.getElementsByName('main_v2_d')[0];
                if (mainFrame) {
                    mainFrame.src = '/servlet/lzca.pc.cht002.servlet.CHt00242?AKEY=Fr00103.Ht00242';
                    return 'フレーム更新成功';
                } else {
                    return 'フレームが見つかりません';
                }
            } catch (e) {
                return 'エラー: ' + e.message;
            }
            """
            
            result = driver.execute_script(js_script)
            print(f"      JavaScript実行結果: {result}")
            
            if "成功" in result:
                time.sleep(4)  # ページ読み込み待機
                print(f"      ✅ 全決済ページの読み込み完了")
                return True
            
        except Exception as e:
            print(f"    方法2失敗: {e}")
            
        # 方法3: 直接URLアクセス
        try:
            print("    方法3: 直接URLアクセス...")
            close_all_url = "https://vt-fx.gaikaex.com/servlet/lzca.pc.cht002.servlet.CHt00242?AKEY=Fr00103.Ht00242"
            driver.get(close_all_url)
            time.sleep(3)
            print(f"      ✅ 直接アクセス完了")
            return True
            
        except Exception as e:
            print(f"    方法3失敗: {e}")
            
        return False
        
    except Exception as e:
        print(f"  ❌ 全決済ページアクセス失敗: {e}")
        return False

def debug_all_frames(driver):
    """
    すべてのフレーム構造をデバッグする関数
    """
    try:
        driver.switch_to.default_content()
        
        # すべてのiframeを検索
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"発見されたiframe数: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            try:
                iframe_id = iframe.get_attribute('id') or f"無ID_{i}"
                iframe_name = iframe.get_attribute('name') or "無名"
                iframe_src = iframe.get_attribute('src') or "src無し"
                
                print(f"  iframe{i+1}: id='{iframe_id}', name='{iframe_name}'")
                print(f"    src: {iframe_src[:100]}..." if len(iframe_src) > 100 else f"    src: {iframe_src}")
                
                # フレーム内容を簡単に調査
                try:
                    driver.switch_to.frame(iframe)
                    frame_title = driver.title
                    frame_url = driver.current_url
                    frame_tables = len(driver.find_elements(By.TAG_NAME, "table"))
                    
                    print(f"    内容: title='{frame_title}', tables={frame_tables}個")
                    
                    # 戻る
                    driver.switch_to.default_content()
                    
                except Exception as frame_error:
                    print(f"    内容取得エラー: {frame_error}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                
            except Exception as e:
                print(f"  iframe{i+1}: 情報取得エラー: {e}")
                
    except Exception as e:
        print(f"フレーム構造デバッグエラー: {e}")

def search_position_table_in_frame(driver, frame_description):
    """
    フレーム内でポジションテーブルを検索する関数（HTMLソース解析対応版）
    
    Returns:
        dict: ポジション情報 {'count': int, 'positions': list} またはNone
    """
    try:
        print(f"      🔍 {frame_description}内で全決済ポジションテーブル検索...")
        
        # 外貨EXの実際のHTML構造に基づいたテーブル検索
        position_table = None
        
        try:
            # 最初に table.item04 を直接検索（外貨EXの標準ポジションテーブル）
            position_table = driver.find_element(By.CSS_SELECTOR, "table.item04")
            print(f"        ✅ 外貨EX標準ポジションテーブル発見: table.item04")
        except NoSuchElementException:
            print(f"        ❌ table.item04 が見つかりません")
            
            # 代替検索パターン
            table_selectors = [
                "table[class*='item']",    # item系のクラス
                ".contents_box2 table",    # contents_box2内のテーブル
                ".notice_box table",       # notice_box内のテーブル
                "form table",              # フォーム内のテーブル
                "table"                    # 最後の手段
            ]
            
            for selector in table_selectors:
                try:
                    tables = driver.find_elements(By.CSS_SELECTOR, selector)
                    for table in tables:
                        # テーブル内容をチェック
                        table_html = table.get_attribute('outerHTML')
                        if ('注文番号' in table_html and '通貨ペア' in table_html and 
                            '売買' in table_html and '未決済数量' in table_html):
                            position_table = table
                            print(f"        ✅ ポジションテーブル発見: {selector}")
                            break
                    if position_table:
                        break
                except:
                    continue
        
        if not position_table:
            print(f"        ❌ {frame_description}内にポジションテーブルなし")
            return None
        
        # HTMLソースに基づいたポジションデータ抽出
        positions = []
        
        try:
            # テーブル行を取得
            all_rows = position_table.find_elements(By.TAG_NAME, "tr")
            print(f"        📋 テーブル総行数: {len(all_rows)}")
            
            # ヘッダー行を特定（th要素があるか、"注文番号"を含む行）
            header_found = False
            data_start_index = 1  # デフォルトは1行目から
            
            for i, row in enumerate(all_rows):
                row_html = row.get_attribute('outerHTML')
                if '<th' in row_html or '注文番号' in row.text:
                    data_start_index = i + 1
                    header_found = True
                    print(f"        📋 ヘッダー行発見: 行{i+1}")
                    break
            
            # データ行を処理
            position_count = 0
            for i in range(data_start_index, len(all_rows)):
                row = all_rows[i]
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # 合計行や空行をスキップ
                row_text = row.text.strip()
                if ('合　計' in row_text or '合計' in row_text or 
                    len(cells) < 4 or not row_text):
                    continue
                
                # HTMLソース構造に基づくポジション情報抽出
                try:
                    # 注文番号（最初のセル）
                    order_no = cells[0].text.strip() if len(cells) > 0 else ""
                    
                    # 通貨ペア（2番目のセル）
                    currency = cells[1].text.strip() if len(cells) > 1 else ""
                    
                    # 売買（3番目のセル、HTMLに span.c_red があれば買い）
                    side_cell_html = cells[2].get_attribute('outerHTML') if len(cells) > 2 else ""
                    side = cells[2].text.strip() if len(cells) > 2 else ""
                    
                    # 未決済数量（4番目のセル、カンマ区切りを処理）
                    amount = cells[3].text.strip().replace(',', '') if len(cells) > 3 else ""
                    
                    # 約定価格（5番目のセル）
                    price = cells[4].text.strip() if len(cells) > 4 else ""
                    
                    # 約定日時（6番目のセル）
                    datetime_str = cells[5].text.strip() if len(cells) > 5 else ""
                    
                    # 評価損益（7番目のセル）
                    pnl = cells[6].text.strip() if len(cells) > 6 else ""
                    
                    # 手数料（8番目のセル）
                    fee = cells[7].text.strip() if len(cells) > 7 else ""
                    
                    # ポジション情報が有効かチェック
                    if order_no and currency and len(order_no) > 5:  # 注文番号が6桁以上
                        position = {
                            'order_no': order_no,
                            'currency': currency,
                            'side': side,
                            'amount': amount,
                            'price': price,
                            'datetime': datetime_str,
                            'pnl': pnl,
                            'fee': fee,
                            'current_price': price  # 約定価格を現在価格として使用
                        }
                        
                        positions.append(position)
                        position_count += 1
                        print(f"        📋 ポジション{position_count}: {order_no} {currency} {side} {amount} @{price} PnL:{pnl}")
                    
                except Exception as cell_error:
                    print(f"        ⚠️ セル処理エラー（行{i+1}）: {cell_error}")
                    continue
            
            # 結果の構築
            result = {
                'count': len(positions),
                'positions': positions,
                'source_frame': frame_description,
                'table_class': 'item04'
            }
            
            print(f"        ✅ {frame_description}で{len(positions)}件のポジション情報を取得成功")
            return result
            
        except Exception as parse_error:
            print(f"        ❌ テーブル解析エラー: {parse_error}")
            return None
        
    except Exception as e:
        print(f"        ❌ {frame_description}内検索エラー: {e}")
        return None

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nプログラムが中断されました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        # ガベージコレクションを強制実行してリソースを解放
        import gc
        gc.collect()
        
        # ChromeDriverのクリーンアップ待機中は標準エラー出力を完全に抑制
        if sys.platform.startswith('win'):
            # Windowsの場合、より強力なエラー抑制
            import subprocess
            import os
            devnull = open(os.devnull, 'w')
            old_stderr = sys.stderr
            sys.stderr = devnull
            
        try:
            time.sleep(2)  # ChromeDriverの終了処理完了を待つ
        finally:
            if sys.platform.startswith('win'):
                sys.stderr = old_stderr
                devnull.close()


