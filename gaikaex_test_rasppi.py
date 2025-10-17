# 外貨EXにChromeDriverでログインして、為替レートを取得するサンプルコード
# 事前にChromeDriverをインストールしておくこと

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import platform
import sys


# ログイン処理
def login_gaikaex(driver, login_id, password):
    login_url = "https://vt-fx.gaikaex.com/servlet/login"
    driver.get(login_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LoginID")))
    driver.find_element(By.ID, "LoginID").send_keys(login_id)
    driver.find_element(By.ID, "Pass").send_keys(password)
    driver.find_element(By.NAME, "loginBtn").click()
    time.sleep(3)
    print("ログイン後タイトル:", driver.title)
    print("ログイン成功。Ctrl+Cで終了します")


def open_realtime_order(driver, timeout=5):
    try:
        # まず新規注文メニューへ移動（必要ならメインメニューframeを操作）
        try:
            navigate_to_new_order(driver, timeout=timeout)
        except Exception:
            pass
            try:
                driver.get('https://vt-fx.gaikaex.com/servlet/lzca.pc.cht001.servlet.CHt00102')
            except Exception:
                pass

    # iframe があるか探す（iframe2 / iframe1 など）
        # 優先的に iframe2 を探して切り替える
        try:
            iframe = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#iframe2, iframe[name='iframe2'], iframe.CHt00102_frame1_v2"))
            )
            driver.switch_to.frame(iframe)
            time.sleep(0.3)
            print("iframe2 に切り替えました")
            # このフレームが「確認」モーダルを表示しているか確認
            confirm_present = False
            try:
                # ドキュメントタイトルに「確認」が含まれるか
                title = driver.execute_script("return document.title || '';")
                if title and '確認' in title:
                    confirm_present = True
            except Exception:
                pass
            if not confirm_present:
                try:
                    # h5 に「確認」が表示される構造を探す
                    el = driver.find_elements(By.XPATH, ".//h5[contains(normalize-space(.),'確認')]")
                    if el and len(el) > 0:
                        confirm_present = True
                except Exception:
                    pass

            if not confirm_present:
                print('確認モーダルが見つからなかったため、OKクリック処理をスキップします')
            else:
                # 初回メッセージのOKボタンがある場合はクリック（より堅牢に）
                try:
                    time.sleep(0.2)
                    clicked_ok = False
                    preferred_ids = ["entry_save", "offset_save", "realtime_save"]
                    for pid in preferred_ids:
                        try:
                            el = WebDriverWait(driver, 1).until(
                                EC.element_to_be_clickable((By.ID, pid))
                            )
                            el.click()
                            print(f'初回メッセージのボタン({pid})をクリックしました')
                            clicked_ok = True
                            break
                        except Exception:
                            continue

                    # 汎用候補を待機付きで検索
                    if not clicked_ok:
                        ok_xpath_candidates = [
                            ".//button[contains(normalize-space(.),'OK')]",
                            ".//button[contains(normalize-space(.),'確認')]",
                            ".//button[contains(normalize-space(.),'同意')]",
                            ".//button[contains(normalize-space(.),'閉じる')]",
                            ".//input[@type='button' and contains(@value,'OK')]",
                            ".//input[@type='button' and contains(@value,'確認')]",
                            ".//input[@type='button' and contains(@value,'同意')]",
                            ".//a[contains(normalize-space(.),'OK')]",
                            ".//a[contains(normalize-space(.),'確認')]",
                        ]
                        for xpath in ok_xpath_candidates:
                            try:
                                el = WebDriverWait(driver, 1).until(
                                    EC.element_to_be_clickable((By.XPATH, xpath))
                                )
                                el.click()
                                print('初回メッセージのOKをクリックしました (xpath)')
                                clicked_ok = True
                                break
                            except Exception:
                                continue

                    # 最終フォールバック: ページ側のJSで用意されている保存関数を呼ぶ
                    if not clicked_ok:
                        # まず要素をJSで直接クリックしてみる
                        try:
                            driver.execute_script("var e = document.getElementById('entry_save'); if(e) e.click();")
                            print('entry_save に対してJS clickを実行しました')
                            clicked_ok = True
                        except Exception:
                            pass

                    # チェックボックスをONにしてから再度クリック（ユーザー選択を模倣）
                    if not clicked_ok:
                        try:
                            driver.execute_script("var c = document.getElementById('checkConfirm_entry'); if(c) { c.checked = true; c.dispatchEvent(new Event('change')); }")
                            driver.execute_script("var e = document.getElementById('entry_save'); if(e) e.click();")
                            print('checkConfirm_entry をONにして entry_save をJSクリックしました')
                            clicked_ok = True
                        except Exception:
                            pass

                    # 最後の手段: g_NS_entry._saveDisclaim_rt() を呼ぶ
                    if not clicked_ok:
                        try:
                            has_fn = driver.execute_script("return (typeof g_NS_entry !== 'undefined' && typeof g_NS_entry._saveDisclaim_rt === 'function');")
                            if has_fn:
                                driver.execute_script("g_NS_entry._saveDisclaim_rt();")
                                print('g_NS_entry._saveDisclaim_rt() を呼び出しました')
                                clicked_ok = True
                        except Exception:
                            pass

                    # クリックしたらモーダルが消えるのを待つ（短時間）
                    if clicked_ok:
                        try:
                            WebDriverWait(driver, 2).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, '#disclaimer-modal-content_entry, #disclaimer-modal-content_offset, .popup_area_disclaimer'))
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
            return True
        except Exception:
            # 代替: 任意のiframeを探して切り替え
            try:
                any_iframe = driver.find_element(By.TAG_NAME, 'iframe')
                driver.switch_to.frame(any_iframe)
                print('最初のiframeに切り替えました（代替）')
                time.sleep(10)
                return True
            except Exception as e:
                print('iframe に切り替えられませんでした:', e)
                return False
    except Exception as e:
        print('open_realtime_order エラー:', e)
        return False


def place_realtime_order(driver, pair_id=None, side='buy', volume=None, execute=False, timeout=3):
    """
    リアルタイム注文フォームの要素を調査し（デバッグ表示）、
    必要な場合はフィールドに値を設定して注文ボタンを押す（execute=True）関数。

    注意: デフォルトでは execute=False のため実際の発注は行いません。
    """
    # iframeへ移動
    ok = open_realtime_order(driver, timeout=timeout)
    if not ok:
        print('リアルタイム注文画面へ移動できませんでした')
        return False

    # フォーム内のinput/select/buttonを列挙して表示（診断用）
    try:
        inputs = driver.find_elements(By.CSS_SELECTOR, 'input, select, button, textarea')
        print(f'フォーム内要素数: {len(inputs)}')
        for i, el in enumerate(inputs[:50]):
            try:
                t = el.tag_name
                _id = el.get_attribute('id') or ''
                _name = el.get_attribute('name') or ''
                _type = el.get_attribute('type') or ''
                text = el.text.strip()[:40]
                val = el.get_attribute('value') or ''
                print(f"{i+1:02d}. <{t}> id='{_id}' name='{_name}' type='{_type}' value='{val}' text='{text}'")
            except Exception:
                continue
    except Exception as e:
        print('フォーム要素の取得に失敗:', e)

    # 簡易ヒューリスティックでフィールドに値を入れてみる（存在すれば）
    def safe_set(selector_list, value, by=By.NAME):
        for sel in selector_list:
            try:
                el = driver.find_element(by, sel)
                tag = el.tag_name
                if tag == 'select':
                    from selenium.webdriver.support.ui import Select
                    Select(el).select_by_value(str(value))
                else:
                    el.clear()
                    el.send_keys(str(value))
                print(f"セット: {sel} = {value}")
                return True
            except Exception:
                continue
        return False

    # 通貨ペア指定 (候補: 'P001', 'pair', 'currency'など)
    if pair_id is not None:
        safe_set(['P001', 'pair', 'currency', 'P002'], pair_id, By.NAME)
    # 売買指定 (buy/sell)。フォームに合うname/idを試す
    if side:
        safe_set(['side', 'buySell', 'P003', 'orderType'], side, By.NAME)
    # 数量
    if volume is not None:
        safe_set(['volume', 'qty', 'amount', 'P004'], volume, By.NAME)

    # ボタン実行（execute=True の場合のみ）
    if execute:
        # まず発注ボタンを探す候補
        btn_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "input[value*='注文']",
            "button:contains('注文')"
        ]
        clicked = False
        for sel in btn_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                btn.click()
                print('発注ボタンをクリックしました:', sel)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            print('発注ボタンが見つかりませんでした。要素一覧を確認してください。')
    else:
        print('execute=False のため、実際の発注は行いませんでした。')

    # フレームから戻る
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    return True


def click_realtime_and_accept(driver, timeout=5):
    """
    ページの「リアルタイム」タブをクリックして、表示された iframe 内の
    確認モーダルがあれば OK を自動でクリックするユーティリティ。
    """
    try:
        # まずナビをクリックしてリアルタイムを開く
        ok = navigate_to_new_order(driver, timeout=timeout)
        if not ok:
            print('リアルタイムタブのクリックに失敗しました')
            return False

        # iframe2 に切り替え（open_realtime_order と同様のセレクタ）
        try:
            iframe = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#iframe2, iframe[name='iframe2'], iframe.CHt00102_frame1_v2"))
            )
            driver.switch_to.frame(iframe)
            time.sleep(0.3)
        except Exception as e:
            print('iframe2 に切り替えられませんでした:', e)
            return False

        # フレーム内のタイトルや h5 を見て '確認' があれば OK を押す
        confirm_present = False
        try:
            title = driver.execute_script("return document.title || '';")
            if title and '確認' in title:
                confirm_present = True
        except Exception:
            pass
        if not confirm_present:
            try:
                el = driver.find_elements(By.XPATH, ".//h5[contains(normalize-space(.),'確認')]")
                if el and len(el) > 0:
                    confirm_present = True
            except Exception:
                pass

        if not confirm_present:
            print('確認モーダルは見つかりませんでした')
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            return True

        # OK クリック（open_realtime_order で行っている手順を再利用）
        # まずモーダルのコンテナが表示されているかを確認して、内部のOKをJSでクリック
        try:
            visible_entry = driver.execute_script("var el = document.getElementById('disclaimer-modal-content_entry'); return el && window.getComputedStyle(el).display !== 'none' && el.className.indexOf('displayNone') === -1;")
            if visible_entry:
                try:
                    driver.execute_script("var b = document.getElementById('entry_save'); if(b) b.click();")
                    print('モーダルコンテナ(disclaimer-modal-content_entry)内の entry_save をクリックしました')
                    clicked_ok = True
                except Exception:
                    pass
        except Exception:
            pass
        try:
            visible_offset = driver.execute_script("var el = document.getElementById('disclaimer-modal-content_offset'); return el && window.getComputedStyle(el).display !== 'none' && el.className.indexOf('displayNone') === -1;")
            if visible_offset and not clicked_ok:
                try:
                    driver.execute_script("var b = document.getElementById('offset_save'); if(b) b.click();")
                    print('モーダルコンテナ(disclaimer-modal-content_offset)内の offset_save をクリックしました')
                    clicked_ok = True
                except Exception:
                    pass
        except Exception:
            pass

        clicked_ok = False
        preferred_ids = ["entry_save", "offset_save", "realtime_save"]
        for pid in preferred_ids:
            try:
                el = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.ID, pid))
                )
                el.click()
                print(f'初回メッセージのボタン({pid})をクリックしました')
                clicked_ok = True
                break
            except Exception:
                continue

        if not clicked_ok:
            ok_xpath_candidates = [
                ".//button[contains(normalize-space(.),'OK')]",
                ".//button[contains(normalize-space(.),'確認')]",
                ".//button[contains(normalize-space(.),'同意')]",
                ".//button[contains(normalize-space(.),'閉じる')]",
                ".//input[@type='button' and contains(@value,'OK')]",
                ".//input[@type='button' and contains(@value,'確認')]",
                ".//input[@type='button' and contains(@value,'同意')]",
                ".//a[contains(normalize-space(.),'OK')]",
                ".//a[contains(normalize-space(.),'確認')]",
            ]
            for xpath in ok_xpath_candidates:
                try:
                    el = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    el.click()
                    print('初回メッセージのOKをクリックしました (xpath)')
                    clicked_ok = True
                    break
                except Exception:
                    continue

        if not clicked_ok:
            try:
                driver.execute_script("var e = document.getElementById('entry_save'); if(e) e.click();")
                print('entry_save に対してJS clickを実行しました')
                clicked_ok = True
            except Exception:
                pass

        if not clicked_ok:
            try:
                driver.execute_script("var c = document.getElementById('checkConfirm_entry'); if(c) { c.checked = true; c.dispatchEvent(new Event('change')); }")
                driver.execute_script("var e = document.getElementById('entry_save'); if(e) e.click();")
                print('checkConfirm_entry をONにして entry_save をJSクリックしました')
                clicked_ok = True
            except Exception:
                pass

        if not clicked_ok:
            try:
                has_fn = driver.execute_script("return (typeof g_NS_entry !== 'undefined' && typeof g_NS_entry._saveDisclaim_rt === 'function');")
                if has_fn:
                    driver.execute_script("g_NS_entry._saveDisclaim_rt();")
                    print('g_NS_entry._saveDisclaim_rt() を呼び出しました')
                    clicked_ok = True
            except Exception:
                pass

        # モーダル消失待ち
        if clicked_ok:
            try:
                WebDriverWait(driver, 2).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, '#disclaimer-modal-content_entry, #disclaimer-modal-content_offset, .popup_area_disclaimer'))
                )
            except Exception:
                pass

        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return True
    except Exception as e:
        print('click_realtime_and_accept エラー:', e)
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return False


def navigate_to_new_order(driver, timeout=5):
    """
    メインメニュー（mainMenu iframe）から「新規注文」へ遷移するユーティリティ。
    新規注文が開けたら True を返す。
    """
    try:
        driver.switch_to.default_content()
        # まず、現在のドキュメント内のナビ（settlement_navi）を探し、「リアルタイム」リンクをクリックする
        try:
            navs = driver.find_elements(By.CSS_SELECTOR, '.settlement_navi a, .settlement_navi li a')
            for a in navs:
                try:
                    txt = a.text.strip()
                    if 'リアルタイム' in txt or '新規注文' in txt:
                        a.click()
                        print('ページ内ナビからリアルタイムをクリックしました:', txt)
                        time.sleep(0.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # 次に mainMenu フレームに切り替え（旧実装）
        try:
            menu_iframe = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, 'mainMenu'))
            )
            driver.switch_to.frame(menu_iframe)
            time.sleep(0.2)
            # mainMenu内のリンクを探してクリック
            links = driver.find_elements(By.TAG_NAME, 'a')
            # まず onclick/href に CHt00102 を含むものを優先
            for a in links:
                try:
                    onclick = a.get_attribute('onclick') or ''
                    href = a.get_attribute('href') or ''
                    if 'CHt00102' in onclick or 'CHt00102' in href:
                        a.click()
                        print('mainMenu: CHt00102 を参照するリンクをクリックしました')
                        time.sleep(0.5)
                        driver.switch_to.default_content()
                        return True
                except Exception:
                    continue
            # 次にテキストベースで探す
            for a in links:
                try:
                    txt = a.text.strip()
                    if '新規注文' in txt or 'リアルタイム' in txt:
                        a.click()
                        print('mainMenu: 新規注文リンクをクリックしました:', txt)
                        time.sleep(0.5)
                        driver.switch_to.default_content()
                        return True
                except Exception:
                    continue
        except Exception as e:
            print('mainMenu iframe が見つかりません:', e)

        # 最後の手段: 直接URLを開く
        try:
            driver.switch_to.default_content()
            driver.get('https://vt-fx.gaikaex.com/servlet/lzca.pc.cht001.servlet.CHt00102')
            time.sleep(0.5)
            return True
        except Exception as e:
            print('直接遷移も失敗:', e)
            return False
    except Exception as e:
        print('navigate_to_new_order エラー:', e)
        return False

# ドル/円レート監視処理（例：10秒ごとに取得して表示）
def monitor_usdjpy_rate(driver):
    import csv
    try:
        bid_list = []
        ask_list = []
        minute_start = None
        import os
        # CSVファイル名は記録開始日時を付与（最初に書き込むタイミングで決定）
        base_name = "usdjpy_rate_log"
        csv_file = None
        print("1分ごとにBid/Askの開始値・終値・最高値・最小値を記録します。Ctrl+Cで終了")
        while True:
            try:
                driver.switch_to.default_content()
                time.sleep(0.1)
                try:
                    priceboard_iframe = driver.find_element(By.CSS_SELECTOR, "iframe#priceboard,iframe[name='priceboard']")
                    driver.switch_to.frame(priceboard_iframe)
                    time.sleep(0.1)
                except Exception:
                    pass
                try:
                    board_iframe = driver.find_element(By.CSS_SELECTOR, "iframe#boardIframe,iframe[name='boardIframe']")
                    driver.switch_to.frame(board_iframe)
                    time.sleep(0.1)
                except Exception:
                    pass
                bid, ask = None, None
                # hidden input
                try:
                    bid = driver.find_element(By.ID, "bid2").get_attribute("value")
                    ask = driver.find_element(By.ID, "ask2").get_attribute("value")
                except Exception:
                    pass
                # ID要素
                if bid is None or ask is None:
                    try:
                        bid_main = driver.find_element(By.ID, "bidRate2").text.strip()
                        bid_small = driver.find_element(By.ID, "bidRateSmall2").text.strip()
                        ask_main = driver.find_element(By.ID, "askRate2").text.strip()
                        ask_small = driver.find_element(By.ID, "askRateSmall2").text.strip()
                        bid = f"{bid_main}.{bid_small}"
                        ask = f"{ask_main}.{ask_small}"
                    except Exception:
                        pass
                # JS
                if bid is None or ask is None:
                    try:
                        bid_js = driver.execute_script("return document.getElementById('bid2') ? document.getElementById('bid2').value : null;")
                        ask_js = driver.execute_script("return document.getElementById('ask2') ? document.getElementById('ask2').value : null;")
                        if bid_js and ask_js:
                            bid = bid_js
                            ask = ask_js
                    except Exception:
                        pass
                now = time.localtime()
                now_str = time.strftime('%Y-%m-%d %H:%M:%S', now)
                sec = now.tm_sec
                # レート取得できた場合のみ記録
                if bid is not None and ask is not None:
                    try:
                        bid_val = float(bid)
                        ask_val = float(ask)
                    except ValueError:
                        print(f"{now_str} レート値変換失敗: Bid={bid} Ask={ask}")
                        time.sleep(0.5)
                        continue
                    print(f"{now_str} Bid: {bid_val} Ask: {ask_val}")
                    # 秒が00なら新しい1分を開始
                    if sec == 0:
                        if bid_list and ask_list:
                            # CSVファイル名が未決定なら、現在時刻を基に作成
                            if csv_file is None:
                                start_ts = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                                csv_file = f"{base_name}_{start_ts}.csv"
                                # ヘッダ追加
                                with open(csv_file, "w", newline="") as hf:
                                    hwriter = csv.writer(hf)
                                    hwriter.writerow([
                                        "datetime", "bid_open", "bid_close", "bid_high", "bid_low",
                                        "ask_open", "ask_close", "ask_high", "ask_low"
                                    ])
                            # 直前の1分間の統計をCSVに記録
                            with open(csv_file, "a", newline="") as f:
                                writer = csv.writer(f)
                                # Bid: 開始値, 終値, 最高値, 最小値
                                bid_open = bid_list[0]
                                bid_close = bid_list[-1]
                                bid_high = max(bid_list)
                                bid_low = min(bid_list)
                                # Ask: 開始値, 終値, 最高値, 最小値
                                ask_open = ask_list[0]
                                ask_close = ask_list[-1]
                                ask_high = max(ask_list)
                                ask_low = min(ask_list)
                                # 日付, 時刻, Bid, Ask
                                # 1分マイナス補正
                                import datetime
                                dt_now = datetime.datetime(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
                                dt_minus1 = dt_now - datetime.timedelta(minutes=1)
                                writer.writerow([
                                    dt_minus1.strftime('%Y-%m-%d %H:%M'),
                                    f"{bid_open:.3f}", f"{bid_close:.3f}", f"{bid_high:.3f}", f"{bid_low:.3f}",
                                    f"{ask_open:.3f}", f"{ask_close:.3f}", f"{ask_high:.3f}", f"{ask_low:.3f}"
                                ])
                            print(f"{now_str} 1分間の統計をCSVに記録しました")
                        # 新しいリストで1分間記録開始
                        bid_list = [bid_val]
                        ask_list = [ask_val]
                        minute_start = now_str
                    else:
                        bid_list.append(bid_val)
                        ask_list.append(ask_val)
                time.sleep(0.5)
            except Exception as e:
                print("レート取得処理で例外:", e)
                time.sleep(1)
    except KeyboardInterrupt:
        print("終了します。ブラウザを閉じます")
        driver.quit()

def main():
    login_id = "3006316"
    password = "Sutada53"
    options = webdriver.ChromeOptions()
    # ブラウザ実行ファイルは環境変数で上書き可能
    chrome_binary = os.environ.get('CHROME_BINARY')
    if chrome_binary:
        options.binary_location = chrome_binary
    else:
        # Raspberry Pi/Linux の既定場所
        if platform.system() == 'Linux':
            options.binary_location = '/usr/bin/chromium-browser'
        # Windows は通常 binary_location を指定しない（chromedriver が自動でChromeを探す）
    options.add_argument('--no-sandbox')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,800')
    # chromedriver のパスは環境変数で指定可能。未指定時は OS によるデフォルトを使用
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    if not chromedriver_path:
        if platform.system() == 'Windows':
            # Windows のデフォルト想定パス（必要に応じて環境変数で上書きしてください）
            chromedriver_path = r'C:\chromedriver\chromedriver.exe'
        else:
            # Linux / Raspberry Pi
            # Raspberry Pi は arm 系なので通常 /usr/bin/chromedriver を利用
            chromedriver_path = '/usr/bin/chromedriver'
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    try:
        login_gaikaex(driver, login_id, password)
        #monitor_usdjpy_rate(driver)
        # Click the 'リアルタイム' tab and accept the initial confirmation if present
        click_realtime_and_accept(driver)
    except Exception as e:
        print("エラー:", e)
        driver.quit()

if __name__ == "__main__":
    main()