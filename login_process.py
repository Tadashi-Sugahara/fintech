import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# ログイン処理
def login_gaikaex(driver, login_id, password):
    login_url = "https://vt-fx.gaikaex.com/servlet/login"
    driver.get(login_url)
    
    # ログインフォームの読み込み完了を待機
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginID")))
    
    # ログインID入力
    login_id_field = driver.find_element(By.ID, "LoginID")
    login_id_field.clear()  # フィールドをクリア
    time.sleep(0.3)
    login_id_field.send_keys(login_id)
    
    # 入力値確認
    entered_login_id = login_id_field.get_attribute("value")
    print(f"入力されたログインID: {entered_login_id}")
    
    # ログインIDが正しく入力されていない場合はJavaScriptで入力
    if entered_login_id != login_id:
        print("⚠️  ログインIDが正しく入力されていません。JavaScriptで再入力します...")
        driver.execute_script("arguments[0].value = arguments[1];", login_id_field, login_id)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", login_id_field)
        entered_login_id = login_id_field.get_attribute("value")
        print(f"JavaScript入力後のログインID: {entered_login_id}")
    
    # パスワード入力
    password_field = driver.find_element(By.ID, "Pass")
    password_field.clear()  # フィールドをクリア
    time.sleep(0.5)  # 少し待機
    
    # 方法1: 通常のsend_keys
    password_field.send_keys(password)
    
    # 入力値確認（デバッグ用）
    entered_password = password_field.get_attribute("value")
    print(f"入力されたパスワード長: {len(entered_password)} 文字")
    
    # パスワードが正しく入力されていない場合は代替方法を使用
    if len(entered_password) != len(password) or entered_password != password:
        print("⚠️  パスワードが正しく入力されていません。JavaScriptで再入力します...")
        
        # 方法2: JavaScriptで直接値を設定
        driver.execute_script("arguments[0].value = '';", password_field)  # クリア
        time.sleep(0.5)
        driver.execute_script("arguments[0].value = arguments[1];", password_field, password)
        
        # 入力イベントを発火
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password_field)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password_field)
        
        # 再確認
        entered_password = password_field.get_attribute("value")
        print(f"JavaScript入力後のパスワード長: {len(entered_password)} 文字")
        
        # まだ正しく入力されていない場合は一文字ずつ入力
        if len(entered_password) != len(password):
            print("⚠️  JavaScript入力も失敗しました。一文字ずつ入力します...")
            password_field.clear()
            time.sleep(1)
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)
            
            # 最終確認
            entered_password = password_field.get_attribute("value")
            print(f"一文字ずつ入力後のパスワード長: {len(entered_password)} 文字")
    
    # ログインボタンをクリック
    driver.find_element(By.NAME, "loginBtn").click()
    time.sleep(3)
    print("ログイン後タイトル:", driver.title)
    print("ログイン成功。Ctrl+Cで終了します")
