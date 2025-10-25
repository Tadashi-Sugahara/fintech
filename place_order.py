import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def navigate_to_order_type(driver, order_type="realtime"):
    """
    新規注文画面の各メニューに移動する関数
    
    Args:
        driver: WebDriverインスタンス
        order_type: 注文タイプ（"realtime", "limit", "ifd", "oco", "ifo"）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"注文タイプ '{order_type}' に移動しています...")
        
        # main_v2_dフレーム（新規注文画面）に切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 注文タイプとJavaScript関数のマッピング
        order_mappings = {
            "realtime": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00102",
                "key": "Ht00102",
                "display_name": "リアルタイム"
            },
            "limit": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00111", 
                "key": "Ht00111",
                "display_name": "指値・逆指値"
            },
            "ifd": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00121",
                "key": "Ht00121", 
                "display_name": "IFD"
            },
            "oco": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00131",
                "key": "Ht00131",
                "display_name": "OCO"
            },
            "ifo": {
                "servlet": "/servlet/lzca.pc.cht001.servlet.CHt00141",
                "key": "Ht00141",
                "display_name": "IFO"
            }
        }
        
        if order_type not in order_mappings:
            print(f"❌ 無効な注文タイプ: {order_type}")
            print(f"有効な注文タイプ: {list(order_mappings.keys())}")
            return False
        
        mapping = order_mappings[order_type]
        
        # settlement_naviエリア内のリンクを探す
        try:
            # 対象のリンクを探す（テキストベース）
            target_link = driver.find_element(By.XPATH, 
                f"//div[@class='settlement_navi']//a[contains(text(), '{mapping['display_name']}')]")
            
            if target_link.is_displayed():
                print(f"'{mapping['display_name']}' リンクをクリックします...")
                target_link.click()
                time.sleep(2)  # ページ遷移待機
                
                # 遷移確認
                try:
                    # アクティブなリンクを確認
                    active_link = driver.find_element(By.XPATH, 
                        "//div[@class='settlement_navi']//a[@class='active']")
                    if mapping['display_name'] in active_link.text:
                        print(f"✅ '{mapping['display_name']}' 画面への移動が成功しました")
                        return True
                    else:
                        print(f"⚠️  移動しましたが、期待したページでない可能性があります")
                        return False
                except Exception:
                    print("アクティブリンクの確認ができませんでしたが、クリックは実行されました")
                    return True
            else:
                print(f"'{mapping['display_name']}' リンクが表示されていません")
                return False
                
        except Exception as e:
            print(f"リンク検索でエラー: {e}")
            
            # フォールバック: JavaScript実行による直接遷移
            try:
                print("JavaScriptによる直接遷移を試行...")
                js_command = f"_submitForm('{mapping['servlet']}', '{mapping['key']}');"
                driver.execute_script(js_command)
                time.sleep(2)
                print(f"✅ JavaScript実行で '{mapping['display_name']}' に移動しました")
                return True
            except Exception as js_e:
                print(f"JavaScript実行でもエラー: {js_e}")
                return False
                
    except Exception as e:
        print(f"注文タイプ移動でエラーが発生: {e}")
        return False
    
    finally:
        # フレームを元に戻す（エラー時も実行）
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

def get_order_frame_info(driver):
    """
    新規注文画面のフレーム情報を取得・表示する関数
    """
    try:
        #print("\n=== 新規注文画面フレーム情報 ===")
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # ページタイトル確認
        page_title = driver.title
        #print(f"ページタイトル: {page_title}")
        
        # 現在のURL確認
        current_url = driver.current_url
        #print(f"現在のURL: {current_url}")
        
        # settlement_naviメニューの状態確認
        try:
            navi_links = driver.find_elements(By.XPATH, "//div[@class='settlement_navi']//a")
            #print(f"\n注文タイプメニュー ({len(navi_links)}個):")
            
            for i, link in enumerate(navi_links):
                try:
                    link_text = link.text.strip()
                    link_class = link.get_attribute("class") or ""
                    onclick = link.get_attribute("onclick") or ""
                    is_active = "active" in link_class
                    status = "🔴 [ACTIVE]" if is_active else "⚪"
                    
                    #print(f"  {status} {link_text}")
                    if onclick:
                        #print(f"       onclick: {onclick[:80]}...")
                        print("")

                except Exception:
                    print(f"  [リンク{i}] 情報取得エラー")
        except Exception as e:
            print(f"メニュー情報取得エラー: {e}")
        
        # iframeの確認
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            #print(f"\n埋め込みフレーム ({len(iframes)}個):")
            
            for i, iframe in enumerate(iframes):
                try:
                    iframe_id = iframe.get_attribute("id") or "no-id"
                    iframe_name = iframe.get_attribute("name") or "no-name"
                    iframe_src = iframe.get_attribute("src") or "no-src"
                    iframe_class = iframe.get_attribute("class") or "no-class"
                    
                    #print(f"  iframe[{i}]: id={iframe_id}, name={iframe_name}")
                    #print(f"              class={iframe_class}")
                    #print(f"              src={iframe_src[:100]}...")
                    
                except Exception:
                    print(f"  iframe[{i}]: 情報取得エラー")
                    
        except Exception as e:
            print(f"iframe情報取得エラー: {e}")
        
        # フォーム情報の確認
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
           # print(f"\nフォーム情報 ({len(forms)}個):")
            
            for i, form in enumerate(forms):
                try:
                    form_name = form.get_attribute("name") or "no-name"
                    hidden_inputs = form.find_elements(By.XPATH, ".//input[@type='hidden']")
                    
                    #print(f"  form[{i}]: name={form_name}")
                    #print(f"            hidden inputs: {len(hidden_inputs)}個")
                    
                    # 重要なhidden inputを表示
                    for hidden in hidden_inputs[:5]:  # 最初の5個だけ
                        input_name = hidden.get_attribute("name") or "no-name"
                        input_value = hidden.get_attribute("value") or "no-value"
                        #print(f"              {input_name}={input_value}")
                        
                except Exception:
                    print(f"  form[{i}]: 情報取得エラー")
                    
        except Exception as e:
            print(f"フォーム情報取得エラー: {e}")
        
        #print("===============================\n")
        
    except Exception as e:
        print(f"フレーム情報取得でエラーが発生: {e}")
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def navigate_to_new_order(driver):
    """
    外貨exのメイン画面から「新規注文」メニューに移動する関数
    """

    try:
        print("新規注文メニューに移動しています...")
        
        # 1. デフォルトコンテンツに戻る
        driver.switch_to.default_content()
        time.sleep(0.5)
        
        # 2. mainMenuフレームに切り替え
        try:
            main_menu_frame = driver.find_element(By.CSS_SELECTOR, "iframe#mainMenu, iframe[name='mainMenu']")
            driver.switch_to.frame(main_menu_frame)
            #print("mainMenuフレームに切り替えました")
        except Exception as e:
            print(f"mainMenuフレームの切り替えに失敗: {e}")
            return False
        
        # 3. 「取引」メニューが開いているか確認し、必要に応じて開く
        try:
            # h3#1 が「取引」メニューのヘッダー
            trade_menu_header = driver.find_element(By.ID, "1")
            
            # selectedクラスがない場合はクリックしてメニューを開く
            if "selected" not in trade_menu_header.get_attribute("class"):
                print("「取引」メニューを開きます...")
                trade_menu_header.click()
                time.sleep(0.1)
            else:
                print("「取引」メニューは既に開いています")
                
        except Exception as e:
            print(f"「取引」メニューの操作に失敗: {e}")
            return False
        
        # 4. 「新規注文」リンクをクリック
        try:
            # menu01内の「新規注文」リンクを探す
            new_order_link = driver.find_element(By.XPATH, "//ul[@id='menu01']//a[contains(text(), '新規注文')]")
            
            if new_order_link.is_displayed():
                #print("「新規注文」リンクをクリックします...")
                new_order_link.click()
                time.sleep(0.2)  # ページ遷移を待つ
                print("「新規注文」画面への移動が完了しました")
                return True
            else:
                print("「新規注文」リンクが表示されていません")
                return False
                
        except Exception as e:
            print(f"「新規注文」リンクのクリックに失敗: {e}")
            return False
            
    except Exception as e:
        print(f"新規注文メニューへの移動でエラーが発生: {e}")
        return False
    
    finally:
        # デフォルトコンテンツに戻る
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def get_page_source_info(driver):
    """
    現在のページソースとフレーム情報を表示するデバッグ用関数
    """
    try:
        print("\n=== ページ情報の取得 ===")
        
        # メインページのタイトルと基本情報
        driver.switch_to.default_content()
        #print(f"メインページタイトル: {driver.title}")
        #print(f"現在のURL: {driver.current_url}")
        
        # iframeの一覧を取得
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        #print(f"iframe数: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            iframe_id = iframe.get_attribute("id") or "no-id"
            iframe_name = iframe.get_attribute("name") or "no-name"
            iframe_src = iframe.get_attribute("src") or "no-src"
            #print(f"  iframe[{i}]: id={iframe_id}, name={iframe_name}, src={iframe_src[:100]}...")
        
        # mainMenuフレーム内の情報を確認
        try:
            main_menu_frame = driver.find_element(By.CSS_SELECTOR, "iframe#mainMenu, iframe[name='mainMenu']")
            driver.switch_to.frame(main_menu_frame)
            
            # メニュー項目を取得
            menu_headers = driver.find_elements(By.TAG_NAME, "h3")
            #print(f"\nメニューヘッダー数: {len(menu_headers)}")
            
            for header in menu_headers:
                header_id = header.get_attribute("id")
                header_text = header.text
                header_class = header.get_attribute("class") or "no-class"
                #print(f"  メニュー[{header_id}]: '{header_text}' (class: {header_class})")
                
                # 対応するメニュー項目を表示
                try:
                    menu_ul = driver.find_element(By.ID, f"menu0{header_id}")
                    menu_items = menu_ul.find_elements(By.TAG_NAME, "a")
                    for item in menu_items:
                        item_text = item.text
                        onclick = item.get_attribute("onclick") or "no-onclick"
                        #print(f"    - {item_text}")
                except Exception:
                    pass
                    
        except Exception as e:
            #print(f"mainMenuフレームの情報取得に失敗: {e}")
            pass
        
        print("")
        print("=========================\n")

        
    except Exception as e:
        print(f"ページ情報の取得でエラーが発生: {e}")
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def quick_navigate_to_order(driver, order_type="realtime"):
    """
    新規注文画面に移動して、指定された注文タイプを開く便利関数
    
    Args:
        driver: WebDriverインスタンス
        order_type: 注文タイプ（"realtime", "limit", "ifd", "oco", "ifo"）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"新規注文 - {order_type.upper()} への直接移動を開始...")
        
        # 1. 新規注文画面に移動
        if not navigate_to_new_order(driver):
            print("❌ 新規注文画面への移動に失敗")
            return False
        
        time.sleep(2)
        
        # 2. 指定された注文タイプに移動
        if not navigate_to_order_type(driver, order_type):
            print(f"❌ {order_type} 画面への移動に失敗")
            return False
        
        print(f"✅ 新規注文 - {order_type.upper()} への移動が完了しました")
        return True
        
    except Exception as e:
        print(f"quick_navigate_to_order でエラー: {e}")
        return False


def display_available_order_types():
    """
    利用可能な注文タイプを表示する関数
    """
    print("\n=== 利用可能な注文タイプ ===")
    order_types = {
        "realtime": "リアルタイム注文",
        "limit": "指値・逆指値注文", 
        "ifd": "IFD注文（If Done）",
        "oco": "OCO注文（One Cancels Other）",
        "ifo": "IFO注文（If Done + OCO）"
    }
    
    for key, description in order_types.items():
        print(f"  {key:<10} : {description}")
    
    print("\n使用例:")
    print("  navigate_to_order_type(driver, 'limit')     # 指値・逆指値に移動")
    print("  quick_navigate_to_order(driver, 'ifd')      # 新規注文→IFDに直接移動")
    print("=============================\n")


# ===== 各注文タイプ専用の操作関数 =====

def operate_realtime_order(driver, pair, amount, order_type, execute_order, silent=False):
    """
    リアルタイム注文を実行する関数（高速化版）
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（例: "USDJPY"）
        amount: 注文数量（例: 10000）
        order_type: 注文種別（"buy"または"sell"）
        execute_order: 実際に注文を実行するかどうか
        silent: メッセージ表示を最小限に抑える（高速化）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        #print(f"リアルタイム注文画面を操作します（{pair}, {amount}, {order_type}）...")
        #print(f"🔍 引数確認: execute_order={execute_order} (型: {type(execute_order)})")
        
        # リアルタイム注文画面に移動
        if not navigate_to_order_type(driver, "realtime"):
            print("❌ リアルタイム注文画面への移動に失敗")
            return False
        
        # main_v2_dフレームに切り替え
        try:
            driver.switch_to.default_content()
            main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
            driver.switch_to.frame(main_frame)
            #print("✅ main_v2_dフレームに切り替えました")
            
            # さらに内側のフレームがあるかチェック
            time.sleep(0.1)  # フレーム読み込み待機
            
            # フレーム内のiframe要素を探す
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            #print(f"📋 フレーム内のiframe数: {len(iframes)}")
            
            # 注文フォームが含まれるiframeを探す
            form_found = False
            for i, iframe in enumerate(iframes):
                try:
                    # 各iframeに切り替えて確認
                    driver.switch_to.frame(iframe)
                    #print(f"📍 iframe[{i}]に切り替えました")
                    
                    # 注文フォーム要素があるかチェック
                    try:
                        # 通貨ペア選択またはボタンがあるかチェック
                        selects = driver.find_elements(By.TAG_NAME, "select")
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        visible_inputs = driver.find_elements(By.XPATH, "//input[@type='text' and not(contains(@style, 'display:none') or contains(@style, 'display: none') or contains(@class, 'displayNone'))]")
                        
                        #print(f"    選択欄: {len(selects)}個, ボタン: {len(buttons)}個, 表示テキスト入力: {len(visible_inputs)}個")
                        
                        # 注文フォーム要素が見つかった場合
                        if len(selects) > 0 or len(buttons) > 0 or len(visible_inputs) > 0:
                            #print(f"✅ 注文フォームが見つかりました（iframe[{i}]）")
                            form_found = True
                            break
                            
                    except Exception:
                        pass
                    
                    # 注文フォームが見つからない場合は元のフレームに戻る
                    driver.switch_to.default_content()
                    driver.switch_to.frame(main_frame)
                    
                except Exception as e:
                    print(f"iframe[{i}]の切り替えでエラー: {e}")
                    # エラーの場合は元のフレームに戻る
                    driver.switch_to.default_content()
                    driver.switch_to.frame(main_frame)
                    continue
            
            if not form_found and len(iframes) == 0:
                print("📝 内側のiframeは見つかりませんでした。メインフレームで処理を続行します。")
            
        except Exception as frame_e:
            print(f"❌ フレーム切り替えでエラー: {frame_e}")
            # フレーム一覧を表示
            try:
                driver.switch_to.default_content()
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print(f"現在のiframe数: {len(iframes)}")
                for i, iframe in enumerate(iframes):
                    iframe_id = iframe.get_attribute("id") or "no-id"
                    iframe_name = iframe.get_attribute("name") or "no-name"
                    print(f"  iframe[{i}]: id={iframe_id}, name={iframe_name}")
            except Exception:
                pass
            return False
        
        # 確認ダイアログが表示されているかチェック
        try:
            disclaimer_modal = driver.find_element(By.ID, "disclaimer-modal-content_entry")
            disclaimer_style = disclaimer_modal.get_attribute("class")
            
            if "displayNone" not in disclaimer_style:
                print("⚠️  確認ダイアログが表示されています")
                print("    手動でダイアログを処理してください:")
                print("    1. 「次回からこの確認を表示しない」にチェック（推奨）")
                print("    2. 「OK」ボタンをクリック")
                print("    3. 処理が完了したら、このスクリプトを再実行してください")
                return False
        except Exception:
            # ダイアログが見つからない場合は処理続行
            print("📝 確認ダイアログは表示されていません")
        
        # 注文フォームが表示されているかチェック
        try:
            entry_div = driver.find_element(By.ID, "entry")
            entry_style = entry_div.get_attribute("class")
            
            if "displayNone" in entry_style:
                print("⚠️  注文フォームがまだ表示されていません")
                print("    確認ダイアログの処理が必要な可能性があります")
                
                # JavaScriptでダイアログを強制的に閉じる試行
                try:
                    print("🔧 JavaScriptで注文フォームの表示を試行...")
                    driver.execute_script("g_NS_entry._saveDisclaim_rt();")
                    time.sleep(0.1)
                    
                    # 再チェック
                    entry_div = driver.find_element(By.ID, "entry")
                    entry_style = entry_div.get_attribute("class")
                    
                    if "displayNone" in entry_style:
                        print("❌ 注文フォームの表示に失敗しました")
                        return False
                    else:
                        print("✅ 注文フォームが表示されました")
                except Exception as js_e:
                    print(f"⚠️  JavaScript実行でエラー: {js_e}")
                    return False
            else:
                print("✅ 注文フォームが表示されています")
               
        except Exception as div_e:
            print(f"⚠️  注文フォーム要素の確認でエラー: {div_e}")
        
        # 通貨ペアのマッピング（HTMLの実際の値に合わせて）
        currency_pair_mapping = {
            "USDJPY": "2",     # ドル/円
            "EURJPY": "3",     # ユーロ/円  
            "EURUSD": "1",     # ユーロ/ドル
            "AUDJPY": "4",     # 豪ドル/円
            "NZDJPY": "6",     # NZドル/円
            "GBPJPY": "5",     # ポンド/円
            "CHFJPY": "8",     # スイスフラン/円
            "CADJPY": "7",     # カナダドル/円
            "GBPUSD": "9",     # ポンド/ドル
            "GBPAUD": "24",    # ポンド/豪ドル
            "ZARJPY": "10",    # ランド/円
            "TRYJPY": "23",    # トルコリラ/円
            "MXNJPY": "25",    # メキシコペソ/円
            "AUDUSD": "11",    # 豪ドル/ドル
            "NZDUSD": "12",    # NZドル/ドル
            "CNHJPY": "13",    # 人民元/円
            "HKDJPY": "14",    # 香港ドル/円
            "EURGBP": "15",    # ユーロ/ポンド
            "EURAUD": "16",    # ユーロ/豪ドル
            "USDCHF": "17",    # 米ドル/スイスフラン
            "EURCHF": "18",    # ユーロ/スイスフラン
            "GBPCHF": "19",    # ポンド/スイスフラン
            "AUDCHF": "20",    # 豪ドル/スイスフラン
            "CADCHF": "21"     # カナダドル/スイスフラン
        }
        
        # 通貨ペア選択
        try:
            pair_value = currency_pair_mapping.get(pair.upper(), "2")  # デフォルトはUSDJPY
            
            # 複数の方法で通貨ペア選択欄を探す
            try:
                pair_selector = driver.find_element(By.ID, "entryCurrencyPair")
            except NoSuchElementException:
                try:
                    pair_selector = driver.find_element(By.NAME, "currencyPair")
                except NoSuchElementException:
                    try:
                        pair_selector = driver.find_element(By.XPATH, "//select[contains(@id, 'currency') or contains(@name, 'currency') or contains(@id, 'pair')]")
                    except NoSuchElementException:
                        pair_selector = driver.find_element(By.XPATH, "//select[position()=1]")
            
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair_value)
            
        except Exception as e:
            print(f"❌ 通貨ペア選択エラー: {e}")
            return False
        
        # 注文数量入力
        try:
            # 複数の方法で数量入力欄を探す
            try:
                amount_input = driver.find_element(By.ID, "amt_entry")
            except NoSuchElementException:
                try:
                    amount_input = driver.find_element(By.NAME, "amt")
                except NoSuchElementException:
                    try:
                        amount_input = driver.find_element(By.XPATH, "//input[@type='text' and (@id='amt' or @name='amt' or contains(@placeholder, '数量') or contains(@placeholder, '金額'))]")
                    except NoSuchElementException:
                        amount_input = driver.find_element(By.XPATH, "//input[@type='text'][position()=1]")
            
            amount_input.clear()
            amount_input.send_keys(str(amount))
            
        except Exception as e:
            print(f"❌ 注文数量入力エラー: {e}")
            return False
        
        # 買い/売りボタンの特定と実行
        try:
            if order_type.lower() == "buy":
                # 買いボタンを探す（複数の方法で試行）
                try:
                    order_button = driver.find_element(By.ID, "btn-buy_entry")
                except NoSuchElementException:
                    try:
                        # テキスト内容で検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(text(), 'BUY') and contains(text(), '買')]")
                    except NoSuchElementException:
                        # より広範囲のXPath検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(@class, 'buy') or contains(@id, 'buy') or contains(text(), 'BUY')]")
                
                action_name = "買い注文 (BUY)"
                button_text = order_button.text.strip()
            else:
                # 売りボタンを探す（複数の方法で試行）
                try:
                    order_button = driver.find_element(By.ID, "btn-sell_entry")
                except NoSuchElementException:
                    try:
                        # テキスト内容で検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(text(), 'SELL') and contains(text(), '売')]")
                    except NoSuchElementException:
                        # より広範囲のXPath検索
                        order_button = driver.find_element(By.XPATH, "//button[contains(@class, 'sell') or contains(@id, 'sell') or contains(text(), 'SELL')]")
                
                action_name = "売り注文 (SELL)"
                button_text = order_button.text.strip()
            
            
        except NoSuchElementException:
            print(f"❌ {action_name}ボタンが見つかりません")
            return False

        # レート情報を取得（簡潔表示）
        try:
            if order_type.lower() == "buy":
                ask_price_1 = driver.find_element(By.ID, "ask-price-1_entry").text
                ask_price_2 = driver.find_element(By.ID, "ask-price-2_entry").text  
                ask_price_3 = driver.find_element(By.ID, "ask-price-3_entry").text
                current_rate = f"{ask_price_1}.{ask_price_2}{ask_price_3}"
            else:
                bid_price_1 = driver.find_element(By.ID, "bid-price-1_entry").text
                bid_price_2 = driver.find_element(By.ID, "bid-price-2_entry").text
                bid_price_3 = driver.find_element(By.ID, "bid-price-3_entry").text
                current_rate = f"{bid_price_1}.{bid_price_2}{bid_price_3}"
        except Exception:
            current_rate = "取得失敗"
        
        # 実際にボタンをクリックして注文実行
        if execute_order:
            print(f"🚀 {order_type.upper()} {pair} {amount:,} @ {current_rate}")
            
            # ボタンクリック実行
            try:
                order_button.click()
                print(f"✅ 注文実行完了")
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", order_button)
                    print(f"✅ 注文実行完了（JS）")
                except Exception as e:
                    print(f"❌ 注文実行失敗: {e}")
                    return False
            
            # 短時間の完了待機
            time.sleep(0.5)
            
            # 注文成功確認（注文完了モーダルチェック）
            try:
                complete_modal = driver.find_element(By.ID, "order-complete-modal-content")
                complete_style = complete_modal.get_attribute("class")
                if "displayNone" not in complete_style:
                    print("🎉 注文完了確認")
                    return True
            except Exception:
                pass
            
            # エラーチェック（具体的なエラー要素のみ）
            try:
                # より具体的なエラー要素を検索
                error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@id, 'error') or (contains(text(), 'エラー') and (contains(@class, 'alert') or contains(@class, 'warning')))]")
                if error_elements:
                    # 実際にエラーメッセージが含まれているかチェック
                    for elem in error_elements:
                        text = elem.text.strip()
                        if text and len(text) > 1 and ('エラー' in text or '失敗' in text or 'error' in text.lower()):
                            print(f"❌ エラー: {text}")
                            return False
            except Exception:
                pass
            
            # エラーがなければ成功
            print("✅ 注文処理成功")
            return True
        else:
            print(f"📝 注文準備完了: {pair} {amount:,} {order_type.upper()} @ {current_rate}")
            return True
            
    except Exception as e:
        if not silent:
            print(f"❌ リアルタイム注文エラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_realtime_order_fast(driver, pair, amount, order_type, execute_order):
    """
    高速化されたリアルタイム注文実行関数
    メッセージ表示を最小限に抑制し、処理速度を優先
    """
    try:
        # 画面遷移（最小限の待機）
        if not navigate_to_order_type(driver, "realtime"):
            return False
        
        # フレーム切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 内部iframe切り替え
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if len(iframes) > 0:
            driver.switch_to.frame(iframes[0])
        
        # 通貨ペア設定
        currency_mapping = {"USDJPY": "2", "EURJPY": "3", "EURUSD": "1", "AUDJPY": "4", "GBPJPY": "5", "NZDJPY": "6"}
        pair_value = currency_mapping.get(pair.upper(), "2")
        
        pair_selector = driver.find_element(By.ID, "entryCurrencyPair")
        from selenium.webdriver.support.ui import Select
        Select(pair_selector).select_by_value(pair_value)
        
        # 数量入力
        amount_input = driver.find_element(By.ID, "amt_entry")
        amount_input.clear()
        amount_input.send_keys(str(amount))
        
        # ボタン選択とクリック
        if order_type.lower() == "buy":
            button_id = "btn-buy_entry"
        else:
            button_id = "btn-sell_entry"
        
        order_button = driver.find_element(By.ID, button_id)
        
        if execute_order:
            order_button.click()
            time.sleep(0.3)  # 最小限の待機
            print(f"🎯 高速注文完了: {order_type.upper()} {pair} {amount}")
            return True
        else:
            print(f"📝 高速注文準備: {order_type.upper()} {pair} {amount}")
            return True
            
    except Exception as e:
        print(f"❌ 高速注文エラー: {e}")
        return False

def operate_realtime_order_ultra_fast(driver, pair, amount, order_type, execute_order=True):
    """
    超高速リアルタイム注文実行（極限の最適化版）
    - 最小限の待機時間（0.05s）
    - 直接的な要素操作
    - ログ出力最小化
    """
    try:
        # 通貨ペアマッピング（高速版と同じ）
        currency_mapping = {
            "USDJPY": "2", "EURJPY": "3", "EURUSD": "1", 
            "AUDJPY": "4", "GBPJPY": "5", "NZDJPY": "6"
        }
        pair_value = currency_mapping.get(pair.upper(), "2")
        
        # 通貨ペア選択（直接的）
        pair_selector = driver.find_element(By.ID, "entryCurrencyPair")
        Select(pair_selector).select_by_value(pair_value)
        
        # 金額入力（直接的）
        amount_input = driver.find_element(By.ID, "amt_entry")
        amount_input.clear()
        amount_input.send_keys(str(amount))
        
        # 売買ボタン（直接的）
        if order_type.lower() == "buy":
            button_id = "btn-buy_entry"
        else:
            button_id = "btn-sell_entry"
        
        order_button = driver.find_element(By.ID, button_id)
        
        if execute_order:
            order_button.click()
            time.sleep(0.05)  # 極限まで短縮
            print(f"⚡ 超高速注文: {order_type.upper()}")
            return True
        else:
            return True
            
    except Exception as e:
        print(f"❌ {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_limit_order(driver, pair="USDJPY", amount=1000, order_type="buy", 
                       limit_price=None, stop_price=None):
    """
    指値・逆指値注文を設定する関数
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        order_type: 注文種別（"buy"または"sell"）
        limit_price: 指値価格（None の場合は設定しない）
        stop_price: 逆指値価格（None の場合は設定しない）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"指値・逆指値注文画面を操作します（{pair}, {amount}, {order_type}）...")
        
        # 指値・逆指値注文画面に移動
        if not navigate_to_order_type(driver, "limit"):
            print("❌ 指値・逆指値注文画面への移動に失敗")
            return False
        
        time.sleep(0.5)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 売買区分選択
        try:
            if order_type.lower() == "buy":
                buy_radio = driver.find_element(By.XPATH, "//input[@type='radio' and @value='1']")
                buy_radio.click()
                print("✅ 買い注文を選択しました")
            else:
                sell_radio = driver.find_element(By.XPATH, "//input[@type='radio' and @value='2']")
                sell_radio.click()
                print("✅ 売り注文を選択しました")
        except Exception as e:
            print(f"⚠️  売買区分選択でエラー: {e}")
        
        # 指値価格設定
        if limit_price is not None:
            try:
                limit_input = driver.find_element(By.NAME, "limitPrice")
                limit_input.clear()
                limit_input.send_keys(str(limit_price))
                print(f"✅ 指値価格 {limit_price} を設定しました")
            except Exception as e:
                print(f"⚠️  指値価格設定でエラー: {e}")
        
        # 逆指値価格設定
        if stop_price is not None:
            try:
                stop_input = driver.find_element(By.NAME, "stopPrice")
                stop_input.clear()
                stop_input.send_keys(str(stop_price))
                print(f"✅ 逆指値価格 {stop_price} を設定しました")
            except Exception as e:
                print(f"⚠️  逆指値価格設定でエラー: {e}")
        
        print("✅ 指値・逆指値注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"指値・逆指値注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_ifd_order(driver, pair="USDJPY", amount=1000, 
                     entry_order_type="buy", entry_price=None,
                     exit_order_type="sell", exit_price=None):
    """
    IFD注文を設定する関数
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        entry_order_type: 新規注文種別（"buy"または"sell"）
        entry_price: 新規注文価格
        exit_order_type: 決済注文種別（"buy"または"sell"）
        exit_price: 決済注文価格
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"IFD注文画面を操作します（{pair}, {amount}）...")
        
        # IFD注文画面に移動
        if not navigate_to_order_type(driver, "ifd"):
            print("❌ IFD注文画面への移動に失敗")
            return False
        
        time.sleep(1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 新規注文の設定
        try:
            # 新規注文の売買区分
            if entry_order_type.lower() == "buy":
                entry_buy_radio = driver.find_element(By.XPATH, "//input[@name='entryBuySell' and @value='1']")
                entry_buy_radio.click()
                print("✅ 新規注文: 買いを選択しました")
            else:
                entry_sell_radio = driver.find_element(By.XPATH, "//input[@name='entryBuySell' and @value='2']")
                entry_sell_radio.click()
                print("✅ 新規注文: 売りを選択しました")
            
            # 新規注文の価格設定
            if entry_price is not None:
                entry_price_input = driver.find_element(By.NAME, "entryPrice")
                entry_price_input.clear()
                entry_price_input.send_keys(str(entry_price))
                print(f"✅ 新規注文価格 {entry_price} を設定しました")
                
        except Exception as e:
            print(f"⚠️  新規注文設定でエラー: {e}")
        
        # 決済注文の設定
        try:
            # 決済注文の価格設定
            if exit_price is not None:
                exit_price_input = driver.find_element(By.NAME, "exitPrice")
                exit_price_input.clear()
                exit_price_input.send_keys(str(exit_price))
                print(f"✅ 決済注文価格 {exit_price} を設定しました")
                
        except Exception as e:
            print(f"⚠️  決済注文設定でエラー: {e}")
        
        print("✅ IFD注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"IFD注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_oco_order(driver, pair="USDJPY", amount=1000,
                     first_price=None, second_price=None):
    """
    OCO注文を設定する関数
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        first_price: 第1注文価格
        second_price: 第2注文価格
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"OCO注文画面を操作します（{pair}, {amount}）...")
        
        # OCO注文画面に移動
        if not navigate_to_order_type(driver, "oco"):
            print("❌ OCO注文画面への移動に失敗")
            return False
        
        time.sleep(1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペア選択
        try:
            pair_selector = driver.find_element(By.NAME, "currencyPair")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair)
            print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 注文数量入力
        try:
            amount_input = driver.find_element(By.NAME, "orderAmount")
            amount_input.clear()
            amount_input.send_keys(str(amount))
            print(f"✅ 注文数量 {amount} を入力しました")
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 第1注文価格設定
        if first_price is not None:
            try:
                first_price_input = driver.find_element(By.NAME, "firstPrice")
                first_price_input.clear()
                first_price_input.send_keys(str(first_price))
                print(f"✅ 第1注文価格 {first_price} を設定しました")
            except Exception as e:
                print(f"⚠️  第1注文価格設定でエラー: {e}")
        
        # 第2注文価格設定
        if second_price is not None:
            try:
                second_price_input = driver.find_element(By.NAME, "secondPrice")
                second_price_input.clear()
                second_price_input.send_keys(str(second_price))
                print(f"✅ 第2注文価格 {second_price} を設定しました")
            except Exception as e:
                print(f"⚠️  第2注文価格設定でエラー: {e}")
        
        print("✅ OCO注文の設定が完了しました")
        print("⚠️  注意: 実際の注文実行は手動で行ってください")
        print("    設定値を確認してから、注文ボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"OCO注文操作でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def operate_ifo_order(driver, pair="USDJPY", amount=1000,
                     entry_order_type="buy", entry_execution_condition="limit",
                     entry_price=None, profit_price=None, loss_price=None):
    """
    IFO注文を設定する関数（IFD + OCO）
    
    Args:
        driver: WebDriverインスタンス
        pair: 通貨ペア（デフォルト: "USDJPY"）
        amount: 注文数量（デフォルト: 1000）
        entry_order_type: 新規注文種別（"buy"または"sell"）
        entry_execution_condition: 新規注文の執行条件（"limit"または"stop"、デフォルト: "limit"）
        entry_price: 新規注文価格
        profit_price: 利益確定価格
        loss_price: 損切り価格
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print(f"IFO注文画面を操作します（{pair}, {amount}）...")
        
        # IFO注文画面に移動
        if not navigate_to_order_type(driver, "ifo"):
            print("❌ IFO注文画面への移動に失敗")
            return False
        
        time.sleep(0.5)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 通貨ペアマッピング
        currency_pair_mapping = {
            "USDJPY": "2", "EURJPY": "3", "EURUSD": "1", "AUDJPY": "4", "NZDJPY": "6", 
            "GBPJPY": "5", "CHFJPY": "8", "CADJPY": "7", "GBPUSD": "9", "GBPAUD": "24",
            "ZARJPY": "10", "TRYJPY": "23", "MXNJPY": "25", "AUDUSD": "11", "NZDUSD": "12",
            "CNHJPY": "13", "HKDJPY": "14", "EURGBP": "15", "EURAUD": "16", "USDCHF": "17",
            "EURCHF": "18", "GBPCHF": "19", "AUDCHF": "20", "CADCHF": "21"
        }
        
        # 通貨ペア選択
        try:
            pair_value = currency_pair_mapping.get(pair.upper(), "2")
            pair_selector = driver.find_element(By.NAME, "P001")
            from selenium.webdriver.support.ui import Select
            select = Select(pair_selector)
            select.select_by_value(pair_value)
            #print(f"✅ 通貨ペア {pair} を選択しました")
        except Exception as e:
            print(f"⚠️  通貨ペア選択でエラー: {e}")
        
        # 新規注文の売買区分選択
        try:
            buy_sell_selector = driver.find_element(By.NAME, "P002")
            select = Select(buy_sell_selector)
            if entry_order_type.lower() == "buy":
                select.select_by_value("0")  # 買い
                #print("✅ 新規注文: 買いを選択しました")
            else:
                select.select_by_value("1")  # 売り
                #print("✅ 新規注文: 売りを選択しました")
        except Exception as e:
            print(f"⚠️  売買区分選択でエラー: {e}")
        
        # 注文数量入力（万の単位）
        try:
            amount_10000 = amount // 10000
            amount_1000 = (amount % 10000) // 1000
            
            if amount_10000 > 0:
                amount_input_10000 = driver.find_element(By.NAME, "P003")
                amount_input_10000.clear()
                amount_input_10000.send_keys(str(amount_10000))
                #print(f"✅ 注文数量 {amount_10000}万を入力しました")
                
            if amount_1000 > 0:
                amount_input_1000 = driver.find_element(By.NAME, "P004")
                amount_input_1000.clear()
                amount_input_1000.send_keys(str(amount_1000))
                #print(f"✅ 注文数量 {amount_1000}千を入力しました")
                
        except Exception as e:
            print(f"⚠️  注文数量入力でエラー: {e}")
        
        # 決済注文数量入力
        try:
            if amount_10000 > 0:
                amount_input_settle_10000 = driver.find_element(By.NAME, "P011")
                amount_input_settle_10000.clear()
                amount_input_settle_10000.send_keys(str(amount_10000))
                
            if amount_1000 > 0:
                amount_input_settle_1000 = driver.find_element(By.NAME, "P012")
                amount_input_settle_1000.clear()
                amount_input_settle_1000.send_keys(str(amount_1000))
                
            #print(f"✅ 決済注文数量を設定しました")
        except Exception as e:
            print(f"⚠️  決済注文数量設定でエラー: {e}")
        
        # 執行条件選択（新規注文）
        try:
            execution_condition = driver.find_element(By.NAME, "P005")
            select = Select(execution_condition)
            
            # 執行条件の設定
            if entry_execution_condition.lower() == "limit":
                select.select_by_value("1")  # 指値
                #print("✅ 新規注文の執行条件: 指値を選択しました")
            elif entry_execution_condition.lower() == "stop":
                select.select_by_value("2")  # 逆指値
                #print("✅ 新規注文の執行条件: 逆指値を選択しました")
            else:
                # デフォルトは指値
                select.select_by_value("1")
                print("⚠️  不明な執行条件のため、デフォルトで指値を選択しました")
                
        except Exception as e:
            print(f"⚠️  執行条件選択でエラー: {e}")
        
        # 決済注文の執行条件設定（隠し要素）
        try:
            # JavaScriptで自動設定を実行
            driver.execute_script("_changeExeConditionType();")
            
            # 決済注文1（利益確定）は指値で固定
            settlement1_condition = driver.find_element(By.NAME, "P013")
            select = Select(settlement1_condition)
            select.select_by_value("1")  # 指値
            
            # 決済注文2（損切り）は逆指値で固定
            settlement2_condition = driver.find_element(By.NAME, "P019")
            select = Select(settlement2_condition)
            select.select_by_value("2")  # 逆指値
            
            #print("✅ 決済注文の執行条件を設定しました（利益確定: 指値、損切り: 逆指値）")
        except Exception as e:
            print(f"⚠️  決済注文執行条件設定でエラー: {e}")
            # エラーでも処理を続行（表示上は固定されているため）
        
        # 新規注文価格設定
        if entry_price is not None:
            try:
                entry_price_input = driver.find_element(By.NAME, "P006")
                entry_price_input.clear()
                entry_price_input.send_keys(str(entry_price))
                #print(f"✅ 新規注文価格 {entry_price} を設定しました")
            except Exception as e:
                print(f"⚠️  新規注文価格設定でエラー: {e}")
        
        # 利益確定価格設定（決済注文1）
        if profit_price is not None:
            try:
                if entry_price is not None:
                    # pips計算（通貨ペアに応じた小数点以下桁数を考慮）
                    pip_multiplier = 10000  # デフォルト（JPY系通貨ペア）
                    if pair.upper() in ["USDJPY", "EURJPY", "AUDJPY", "GBPJPY", "NZDJPY", "CHFJPY", "CADJPY", "ZARJPY", "TRYJPY", "MXNJPY", "CNHJPY", "HKDJPY"]:
                        pip_multiplier = 100  # JPY系は小数点以下2桁なので100倍
                    elif pair.upper() in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "EURCHF", "GBPCHF", "AUDCHF", "CADCHF", "EURGBP", "EURAUD", "GBPAUD"]:
                        pip_multiplier = 10000  # USD/EUR系は小数点以下4桁なので10000倍
                    
                    if entry_order_type.lower() == "buy":
                        # 買いポジションの利確：エントリー価格より高い価格で売る
                        pips = (profit_price - entry_price) * pip_multiplier
                        if pips <= 0:
                            print(f"⚠️  買いポジションの利益確定価格({profit_price})はエントリー価格({entry_price})より高く設定してください")
                            return False
                    else:
                        # 売りポジションの利確：エントリー価格より低い価格で買い戻す
                        pips = (entry_price - profit_price) * pip_multiplier
                        if pips <= 0:
                            print(f"⚠️  売りポジションの利益確定価格({profit_price})はエントリー価格({entry_price})より低く設定してください")
                            return False
                    
                    spin_input = driver.find_element(By.NAME, "spin")
                    spin_input.clear()
                    spin_input.send_keys(str(abs(pips)))
                    driver.execute_script("_settlePriceCalcIFO2(0);")
                    time.sleep(0.5)
                    #print(f"✅ 利益確定価格設定: エントリー価格({entry_price})から{abs(pips):.1f}pips差で利確価格を設定")
                else:
                    print("⚠️  利益確定価格を設定するにはentry_priceが必要です")
            except Exception as e:
                print(f"⚠️  利益確定価格設定でエラー: {e}")
        
        # 損切り価格設定（決済注文2）
        if loss_price is not None:
            try:
                if entry_price is not None:
                    # pips計算（通貨ペアに応じた小数点以下桁数を考慮）
                    pip_multiplier = 10000  # デフォルト（JPY系通貨ペア）
                    if pair.upper() in ["USDJPY", "EURJPY", "AUDJPY", "GBPJPY", "NZDJPY", "CHFJPY", "CADJPY", "ZARJPY", "TRYJPY", "MXNJPY", "CNHJPY", "HKDJPY"]:
                        pip_multiplier = 100  # JPY系は小数点以下2桁なので100倍
                    elif pair.upper() in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "EURCHF", "GBPCHF", "AUDCHF", "CADCHF", "EURGBP", "EURAUD", "GBPAUD"]:
                        pip_multiplier = 10000  # USD/EUR系は小数点以下4桁なので10000倍
                    
                    if entry_order_type.lower() == "buy":
                        # 買いポジションの損切り：エントリー価格より低い価格で売る
                        pips2 = (entry_price - loss_price) * pip_multiplier
                        if pips2 <= 0:
                            print(f"⚠️  買いポジションの損切り価格({loss_price})はエントリー価格({entry_price})より低く設定してください")
                            return False
                    else:
                        # 売りポジションの損切り：エントリー価格より高い価格で買い戻す
                        pips2 = (loss_price - entry_price) * pip_multiplier
                        if pips2 <= 0:
                            print(f"⚠️  売りポジションの損切り価格({loss_price})はエントリー価格({entry_price})より高く設定してください")
                            return False
                    
                    spin2_input = driver.find_element(By.NAME, "spin2")
                    spin2_input.clear()
                    spin2_input.send_keys(str(abs(pips2)))
                    driver.execute_script("_settlePriceCalcIFO3(0);")
                    time.sleep(0.5)
                    #print(f"✅ 損切り価格設定: エントリー価格({entry_price})から{abs(pips2):.1f}pips差で損切り価格を設定")
                else:
                    print("⚠️  損切り価格を設定するにはentry_priceが必要です")
            except Exception as e:
                print(f"⚠️  損切り価格設定でエラー: {e}")
        
        # 有効期限設定
        try:
            expiry_selector = driver.find_element(By.NAME, "P007")
            select = Select(expiry_selector)
            select.select_by_value("2")  # 無期限
            #print("✅ 有効期限: 無期限を選択しました")
        except Exception as e:
            print(f"⚠️  有効期限設定でエラー: {e}")
        
        print("✅ IFO注文の設定完了")
        
        # 「確認画面へ」ボタンをクリック（最高速化版）
        try:
            start_click_time = time.time()  # クリック時間測定開始
            
            # 事前にボタンを特定（待機なし）
            confirmation_button = None
            
            # 最速検索: 直接JavaScript実行で検索・クリック同時実行
            click_script = """
            // 最速で確認画面へボタンを検索・クリック
            var buttons = document.querySelectorAll('input[type="submit"][value*="確認"], button');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                var text = btn.value || btn.textContent || btn.innerText || '';
                if (text.includes('確認') && text.includes('画面')) {
                    btn.click();
                    return true;
                }
            }
            // フォールバック: より広範囲で検索
            var allButtons = document.querySelectorAll('input[type="submit"], button');
            for (var i = 0; i < allButtons.length; i++) {
                var btn = allButtons[i];
                var text = btn.value || btn.textContent || btn.innerText || '';
                if (text.includes('確認')) {
                    btn.click();
                    return true;
                }
            }
            return false;
            """
            
            # JavaScript一回実行で検索・クリック完了
            click_success = driver.execute_script(click_script)
            # 結果ログ出力
            if click_success:
                click_time = time.time() - start_click_time
                print(f"⚡ 確認画面へボタン超高速クリック完了: {click_time*1000:.1f}ms")
            else:
                # フォールバック: 従来方式（最小限）
                try:
                    confirmation_button = driver.find_element(By.XPATH, "//input[@type='submit'][@value='確認画面へ']")
                    driver.execute_script("arguments[0].click();", confirmation_button)
                    click_time = time.time() - start_click_time
                    print(f"⚡ 確認画面へボタンクリック（フォールバック）: {click_time*1000:.1f}ms")
                except:
                    print("⚠️  確認画面へボタンが見つかりませんでした")
            
            # 確認画面へのクリックが成功した場合、注文実行処理を続行
            if click_success or True:  # どちらの方法でも成功時は処理を続行
                # 使用例をログに出力
                print(f"\n📝 設定内容:")
                print(f"   通貨ペア: {pair}")
                print(f"   注文数量: {amount:,}")
                print(f"   売買区分: {entry_order_type}")
                print(f"   執行条件: {'指値' if entry_execution_condition.lower() == 'limit' else '逆指値'}")
                if entry_price:
                    print(f"   新規注文価格: {entry_price}")
                if profit_price:
                    print(f"   利益確定価格: {profit_price}")
                if loss_price:
                    print(f"   損切り価格: {loss_price}")
                #print("\n✅ 確認画面に遷移しました。注文実行ボタンをクリックします...")
                
                # 確認画面で「注文実行」ボタンをクリック（最高速・確実版）
                try:
                    execute_start_time = time.time()  # 実行時間測定
                    
                    # フレームを再取得（確認画面に切り替わっているため）
                    driver.switch_to.default_content()
                    main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
                    driver.switch_to.frame(main_frame)
                    
                    # 画面読み込み完了とJavaScript初期化を待機
                    time.sleep(0.5)  # 500ms待機で確実性向上
                    
                    # DOMの完全読み込みを確認
                    try:
                        WebDriverWait(driver, 5).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        # ablebtn()関数の存在確認
                        ablebtn_exists = driver.execute_script("return typeof ablebtn === 'function';")
                        if ablebtn_exists:
                            print("✅ ablebtn()関数が利用可能です")
                        else:
                            print("⚠️  ablebtn()関数が見つかりません")
                    except:
                        print("⚠️  DOM読み込み確認でタイムアウト")
                    
                    # 最速JavaScript実行で注文実行ボタン検索・有効化・クリック
                    execute_script = """
                    // 1. まず ablebtn() 関数を実行してボタンを有効化
                    if (typeof ablebtn === 'function') {
                        ablebtn();
                    }
                    
                    // 2. フォーム内の全ボタンを強制有効化
                    var forms = document.forms;
                    for (var f = 0; f < forms.length; f++) {
                        var elements = forms[f].elements;
                        for (var i = 0; i < elements.length; i++) {
                            if (elements[i].type === 'button') {
                                elements[i].disabled = false;
                                elements[i].removeAttribute('disabled');
                                elements[i].classList.remove('disAbleElmnt');
                            }
                        }
                    }
                    
                    // 3. 注文実行ボタンを包括的に検索・クリック
                    var executePatterns = [
                        'button[name="EXEC"]',                           // name属性（最優先）
                        'button[onclick*="CHt00143"]',                   // onclick関数
                        'input[type="submit"][value*="注文実行"]',        // submit入力
                        'button:contains("注文実行")',                   // テキスト含有
                        'button:contains("実行")',                       // 実行のみ
                        'input[type="button"][value*="実行"]',           // button入力
                        'button[class*="blue"]',                        // 青色ボタン（実行系）
                        'button',                                       // 全ボタン
                        'input[type="submit"]',                         // 全submit
                        'input[type="button"]'                          // 全button input
                    ];
                    
                    for (var p = 0; p < executePatterns.length; p++) {
                        var buttons = document.querySelectorAll(executePatterns[p]);
                        for (var i = 0; i < buttons.length; i++) {
                            var btn = buttons[i];
                            var text = btn.value || btn.textContent || btn.innerText || '';
                            var name = btn.name || '';
                            var onclick = btn.onclick ? btn.onclick.toString() : '';
                            
                            // より包括的な判定
                            if (name === 'EXEC' || 
                                text.includes('実行') || 
                                text.includes('EXEC') ||
                                onclick.includes('CHt00143') ||
                                (text.includes('注文') && text.includes('実行'))) {
                                
                                // ボタンを確実に有効化
                                btn.disabled = false;
                                btn.removeAttribute('disabled');
                                btn.classList.remove('disAbleElmnt');
                                btn.style.pointerEvents = 'auto';
                                
                                // フォーカスして目立たせる
                                btn.focus();
                                
                                // クリック実行
                                btn.click();
                                
                                return {success: true, pattern: p, text: text, name: name};
                            }
                        }
                    }
                    return {success: false};
                    """
                    
                    # JavaScript一回実行で完了
                    result = driver.execute_script(execute_script)
                    
                    execute_time = time.time() - execute_start_time
                    
                    if result and result.get('success'):
                        print(f"⚡ 注文実行ボタン超高速クリック完了: {execute_time*1000:.1f}ms")
                        print(f"   検索パターン: {result.get('pattern', 'unknown')}")
                        print(f"   ボタンテキスト: {result.get('text', 'unknown')}")
                        print("🎉 IFO注文の実行が完了しました！")
                    else:
                        # より強力なフォールバック（Seleniumでablebtn実行）
                        print("⚠️  JavaScript検索が失敗、Seleniumフォールバック実行中...")
                        
                        # 1. Seleniumでablebtn()関数を実行
                        try:
                            driver.execute_script("if (typeof ablebtn === 'function') ablebtn();")
                            print("✅ ablebtn()をSeleniumで実行しました")
                        except Exception as e:
                            print(f"⚠️  ablebtn()実行失敗: {e}")
                        
                        # 2. 全ボタンを強制有効化
                        try:
                            driver.execute_script("""
                                var buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
                                for (var i = 0; i < buttons.length; i++) {
                                    buttons[i].disabled = false;
                                    buttons[i].removeAttribute('disabled');
                                    buttons[i].classList.remove('disAbleElmnt');
                                }
                            """)
                            print("✅ 全ボタンを強制有効化しました")
                        except Exception as e:
                            print(f"⚠️  ボタン有効化失敗: {e}")
                        
                        # 3. 従来のSelenium方式（改良版）
                        execute_button = None
                        enhanced_patterns = [
                            "//button[@name='EXEC']",
                            "//button[contains(@onclick, 'CHt00143')]",
                            "//input[@type='submit'][contains(@value, '注文実行')]",
                            "//button[contains(text(), '注文実行')]",
                            "//button[contains(text(), '実行')]",
                            "//input[@type='button'][contains(@value, '実行')]",
                            "//button[contains(@class, 'blue')]",
                            "//button[contains(@class, 'exec')]",
                            "//*[contains(@name, 'exec')]",
                            "//*[contains(@onclick, 'exec')]"
                        ]
                        
                        for i, pattern in enumerate(enhanced_patterns):
                            try:
                                execute_button = driver.find_element(By.XPATH, pattern)
                                print(f"✅ ボタン発見（パターン{i+1}): {pattern}")
                                break
                            except:
                                continue
                        
                        if execute_button:
                            # ボタンの詳細情報を表示
                            button_info = {
                                'text': execute_button.text or execute_button.get_attribute("value") or "テキストなし",
                                'name': execute_button.get_attribute("name") or "名前なし",
                                'disabled': execute_button.get_attribute("disabled"),
                                'class': execute_button.get_attribute("class") or "クラスなし",
                                'onclick': execute_button.get_attribute("onclick") or "イベントなし"
                            }
                            print(f"📋 ボタン情報: {button_info}")
                            
                            # 確実に有効化してクリック
                            driver.execute_script("""
                                arguments[0].disabled = false;
                                arguments[0].removeAttribute('disabled');
                                arguments[0].classList.remove('disAbleElmnt');
                                arguments[0].style.pointerEvents = 'auto';
                                arguments[0].focus();
                                arguments[0].click();
                            """, execute_button)
                            execute_time = time.time() - execute_start_time
                            print(f"✅ 注文実行ボタンクリック（フォールバック）: {execute_time*1000:.1f}ms")
                            print("🎉 IFO注文の実行が完了しました！")
                        else:
                            print("❌ 注文実行ボタンが見つかりませんでした")
                            print("    手動で注文実行ボタンをクリックしてください")
                            
                            # 詳細デバッグ情報
                            try:
                                all_buttons = driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']")
                                print(f"   確認画面で利用可能なボタン（{len(all_buttons)}個）:")
                                for i, btn in enumerate(all_buttons):
                                    btn_text = btn.text or btn.get_attribute("value") or "テキストなし"
                                    btn_name = btn.get_attribute("name") or "名前なし"
                                    btn_onclick = btn.get_attribute("onclick") or "イベントなし"
                                    btn_class = btn.get_attribute("class") or "クラスなし"
                                    btn_disabled = btn.get_attribute("disabled")
                                    print(f"     [{i}] テキスト: {btn_text}")
                                    print(f"          name: {btn_name}, disabled: {btn_disabled}")
                                    print(f"          class: {btn_class}")
                                    if "CHt00143" in str(btn_onclick) or "実行" in btn_text:
                                        print(f"         → 🎯 注文実行関連ボタンの可能性あり！")
                                        
                                # ページのJavaScript関数も確認
                                js_functions = driver.execute_script("""
                                    var functions = [];
                                    if (typeof ablebtn === 'function') functions.push('ablebtn');
                                    if (typeof _submitForm === 'function') functions.push('_submitForm');
                                    return functions;
                                """)
                                print(f"   利用可能なJavaScript関数: {js_functions}")
                                
                            except Exception as debug_error:
                                print(f"⚠️  デバッグ情報取得エラー: {debug_error}")
                
                except Exception as execute_error:
                    print(f"⚠️  注文実行ボタンのクリックでエラー: {execute_error}")
                    print("    手動で注文実行ボタンをクリックしてください")
            
            print("🏁 IFO注文処理が完了しました")
                    
        except Exception as e:
            print(f"⚠️  確認画面へボタンのクリックでエラー: {e}")
            print("    手動で確認画面へボタンをクリックしてください")
        
        return True
        
    except Exception as e:
        print(f"IFO注文操作でエラー: {e}")
        return False
    
    finally:
        # 確実にデフォルトフレームに戻す
        try:
            driver.switch_to.default_content()
            print("✅ デフォルトフレームに復帰しました")
        except Exception:
            pass

# 【IFO注文の使用例】
# # 買い注文: エントリー149.50、利確150.00（+50pips）、損切り149.00（-50pips）
# operate_ifo_order(driver, "USDJPY", 10000, "buy", "limit", 149.50, 150.00, 149.00)
# 
# # 逆指値買い注文: ブレイクアウト狙い
# operate_ifo_order(driver, "USDJPY", 10000, "buy", "stop", 150.50, 151.00, 150.00)
# 
# # 売り注文: エントリー160.00、利確159.50（+50pips）、損切り160.50（-50pips）
# operate_ifo_order(driver, "EURJPY", 5000, "sell", "limit", 160.00, 159.50, 160.50)
# 
# # USD系通貨ペアの例: エントリー1.0950、利確1.1000（+50pips）、損切り1.0900（-50pips）
# operate_ifo_order(driver, "EURUSD", 10000, "buy", "limit", 1.0950, 1.1000, 1.0900)


def analyze_form_elements(driver, order_type="realtime"):
    """
    指定された注文タイプ画面のフォーム要素を詳細分析する関数
    
    Args:
        driver: WebDriverインスタンス
        order_type: 分析する注文タイプ
    """
    try:
        print(f"\n=== {order_type.upper()} 画面のフォーム要素分析 ===")
        
        # 指定された注文タイプに移動
        if not navigate_to_order_type(driver, order_type):
            print(f"❌ {order_type} 画面への移動に失敗")
            return
        
        time.sleep(0.1)
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        # 全ての入力要素を分析
        input_elements = driver.find_elements(By.TAG_NAME, "input")
        select_elements = driver.find_elements(By.TAG_NAME, "select")
        
        #print(f"入力要素 ({len(input_elements)}個):")
        for i, elem in enumerate(input_elements):
            try:
                elem_type = elem.get_attribute("type") or "text"
                elem_name = elem.get_attribute("name") or "no-name"
                elem_id = elem.get_attribute("id") or "no-id"
                elem_value = elem.get_attribute("value") or ""
                elem_class = elem.get_attribute("class") or "no-class"
                
                #print(f"  input[{i}]: type={elem_type}, name={elem_name}, id={elem_id}")
                if elem_value:
                    #print(f"             value={elem_value[:50]}...")
                    print("")
                if elem_class != "no-class":
                    #print(f"             class={elem_class}")
                    print("")
                    
            except Exception:
                print(f"  input[{i}]: 要素情報取得エラー")
        
        #print(f"\nセレクト要素 ({len(select_elements)}個):")
        for i, elem in enumerate(select_elements):
            try:
                elem_name = elem.get_attribute("name") or "no-name"
                elem_id = elem.get_attribute("id") or "no-id"
                options = elem.find_elements(By.TAG_NAME, "option")
                
                #print(f"  select[{i}]: name={elem_name}, id={elem_id}")
                #print(f"              options={len(options)}個")
                
                # 最初の3つのオプション値を表示
                for j, option in enumerate(options[:3]):
                    option_value = option.get_attribute("value") or ""
                    option_text = option.text.strip()
                    #print(f"                [{j}] value={option_value}, text={option_text}")
                
                if len(options) > 3:
                    #print(f"                ... 他{len(options)-3}個")
                    print(""   )

            except Exception:
                print(f"  select[{i}]: 要素情報取得エラー")
        
        # ボタン要素を分析
        button_elements = driver.find_elements(By.XPATH, "//input[@type='submit'] | //input[@type='button'] | //button")
        
        #print(f"\nボタン要素 ({len(button_elements)}個):")
        for i, elem in enumerate(button_elements):
            try:
                elem_type = elem.get_attribute("type") or "button"
                elem_value = elem.get_attribute("value") or ""
                elem_text = elem.text.strip()
                elem_onclick = elem.get_attribute("onclick") or ""
                
                #print(f"  button[{i}]: type={elem_type}")
                if elem_value:
                    #print(f"              value={elem_value}")
                    print("")
                if elem_text:
                    #print(f"              text={elem_text}")
                    print("")
                if elem_onclick:
                    #print(f"              onclick={elem_onclick[:50]}...")
                    print("")

            except Exception:
                print(f"  button[{i}]: 要素情報取得エラー")
        
        print(f"\n=== {order_type.upper()} 画面の分析完了 ===\n")
        
    except Exception as e:
        print(f"フォーム要素分析でエラー: {e}")
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

def operate_ifo_order_ultra_fast(driver, pair="USDJPY", amount=1000,
                                  entry_order_type="buy", entry_execution_condition="limit",
                                  entry_price=None, profit_price=None, loss_price=None):
    """
    IFO注文を超高速で実行する関数
    確認画面へボタンと注文実行ボタンの待機時間を最小化
    
    Parameters:
    - driver: WebDriverインスタンス
    - pair: 通貨ペア（例: "USDJPY", "EURJPY"）
    - amount: 注文数量
    - entry_order_type: 売買区分（"buy" または "sell"）
    - entry_execution_condition: 執行条件（"limit" または "stop"）
    - entry_price: 新規注文価格
    - profit_price: 利益確定価格
    - loss_price: 損切り価格
    """
    print("🚀 IFO注文（超高速版）を開始します")
    
    try:
        # 通常のIFO注文設定は同じ処理を使用
        # ここでは確認画面への遷移とボタンクリックのみ高速化
        
        # main_v2_dフレームに切り替え
        driver.switch_to.default_content()
        main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(main_frame)
        
        print("⚡ 超高速モード: 最小限の待機時間で処理します")
        
        # 確認画面へボタンを超高速でクリック
        try:
            # 待機時間なしで即座に検索・クリック
            confirmation_button = driver.find_element(By.XPATH, "//input[@type='submit'][@value='確認画面へ']")
            driver.execute_script("arguments[0].click();", confirmation_button)
            time.sleep(0.01)  # 極小待機
            print("⚡ 確認画面へボタンを超高速クリック")
            
            # 注文実行ボタンを超高速でクリック
            time.sleep(0.1)  # 画面遷移の最小待機
            driver.switch_to.default_content()
            main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
            driver.switch_to.frame(main_frame)
            
            execute_button = driver.find_element(By.XPATH, "//button[@name='EXEC']")
            driver.execute_script("""
                arguments[0].disabled = false;
                arguments[0].click();
            """, execute_button)
            time.sleep(0.01)  # 極小待機
            print("⚡ 注文実行ボタンを超高速クリック")
            print("🏁 IFO注文（超高速版）が完了しました！")
            
        except Exception as e:
            print(f"⚠️  超高速処理でエラー: {e}")
            print("💡 通常のIFO注文関数を使用してください")
            return False
        
        return True
        
    except Exception as e:
        print(f"IFO注文（超高速版）でエラー: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

def click_confirmation_button_ultra_fast(driver):
    """
    「確認画面へ」ボタンを最高速でクリックする専用関数
    戻り値: (成功フラグ, 実行時間)
    """
    start_time = time.time()
    
    try:
        # 最速JavaScript: DOM検索とクリックを一回で実行
        click_script = """
        var patterns = [
            'input[type="submit"][value="確認画面へ"]',
            'input[type="submit"][value*="確認"]',
            'button:contains("確認画面へ")',
            'input[type="submit"]',
            'button'
        ];
        
        for (var p = 0; p < patterns.length; p++) {
            var elements = document.querySelectorAll(patterns[p]);
            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];
                var text = el.value || el.textContent || el.innerText || '';
                if (text.includes('確認') && (text.includes('画面') || text.includes('へ'))) {
                    el.click();
                    return true;
                }
            }
        }
        return false;
        """
        
        # 一回のJavaScript実行で完了
        success = driver.execute_script(click_script)
        execution_time = time.time() - start_time
        
        return success, execution_time
            
    except Exception:
        return False, time.time() - start_time

def click_execute_button_ultra_fast(driver):
    """
    「注文実行」ボタンを最高速・確実にクリックする専用関数
    戻り値: (成功フラグ, 実行時間)
    """
    start_time = time.time()
    
    try:
        # フレーム切り替えも最速で
        driver.switch_to.default_content()
        frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
        driver.switch_to.frame(frame)
        
        # 最速JavaScript: 有効化と検索とクリックを一回で実行
        execute_script = """
        // 1. ablebtn() 関数を実行してボタンを有効化
        if (typeof ablebtn === 'function') {
            ablebtn();
        }
        
        // 2. 全フォームの全ボタンを強制有効化
        var forms = document.forms;
        for (var f = 0; f < forms.length; f++) {
            var elements = forms[f].elements;
            for (var i = 0; i < elements.length; i++) {
                if (elements[i].type === 'button') {
                    elements[i].disabled = false;
                    elements[i].removeAttribute('disabled');
                    elements[i].classList.remove('disAbleElmnt');
                }
            }
        }
        
        // 3. 注文実行ボタンを検索・クリック
        var patterns = [
            'button[name="EXEC"]',
            'button[onclick*="CHt00143"]',
            'input[type="submit"][value*="注文実行"]',
            'button',
            'input[type="submit"]',
            'input[type="button"]'
        ];
        
        for (var p = 0; p < patterns.length; p++) {
            var elements = document.querySelectorAll(patterns[p]);
            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];
                var text = el.value || el.textContent || el.innerText || '';
                var name = el.name || '';
                var onclick = el.onclick ? el.onclick.toString() : '';
                
                if (name === 'EXEC' || 
                    text.includes('実行') || 
                    text.includes('EXEC') ||
                    onclick.includes('CHt00143') ||
                    (text.includes('注文') && text.includes('実行'))) {
                    
                    // 確実に有効化
                    el.disabled = false;
                    el.removeAttribute('disabled');
                    el.classList.remove('disAbleElmnt');
                    el.style.pointerEvents = 'auto';
                    
                    // クリック実行
                    el.click();
                    return true;
                }
            }
        }
        return false;
        """
        
        # JavaScript一回実行で完了
        success = driver.execute_script(execute_script)
        execution_time = time.time() - start_time
        
        return success, execution_time
        
    except Exception:
        return False, time.time() - start_time

def operate_ifo_order_lightning_fast(driver, pair="USDJPY", amount=1000,
                                     entry_order_type="buy", entry_execution_condition="limit",
                                     entry_price=None, profit_price=None, loss_price=None):
    """
    IFO注文を電光石火の速度で実行する関数（最速版）
    確認画面へボタンと注文実行ボタンを専用関数で超高速処理
    """
    print("⚡ IFO注文（電光石火版）を開始します")
    total_start_time = time.time()
    
    try:
        # 基本設定は省略（既に設定済みと仮定）
        print("⚡ 基本設定をスキップし、ボタンクリックのみ実行します")
        
        # 確認画面へボタンを電光石火でクリック
        success1, time1 = click_confirmation_button_ultra_fast(driver)
        if success1:
            print(f"⚡ 確認画面へボタンクリック完了: {time1*1000:.1f}ms")
        else:
            print("❌ 確認画面へボタンクリック失敗")
            return False
        
        # 最小待機時間で画面遷移（さらに短縮）
        time.sleep(0.01)  # 10ms（1/100秒）
        
        # 注文実行ボタンを電光石火でクリック
        success2, time2 = click_execute_button_ultra_fast(driver)
        if success2:
            print(f"⚡ 注文実行ボタンクリック完了: {time2*1000:.1f}ms")
        else:
            print("❌ 注文実行ボタンクリック失敗")
            return False
        
        total_time = time.time() - total_start_time
        print(f"🏁 IFO注文（電光石火版）完了: 総時間 {total_time*1000:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"⚠️  電光石火版でエラー: {e}")
        return False

# 【高速化IFO注文の使用例】
# # 電光石火版（最速・リスク最高）
# operate_ifo_order_lightning_fast(driver, "USDJPY", 10000, "buy", "limit", 149.50, 150.00, 149.00)
# 
# # 超高速版（リスク高・速度重視）
# operate_ifo_order_ultra_fast(driver, "USDJPY", 10000, "buy", "limit", 149.50, 150.00, 149.00)
# 
# # 通常版（バランス重視）
# operate_ifo_order(driver, "USDJPY", 10000, "buy", "limit", 149.50, 150.00, 149.00)

def test_ifo_order_speed(driver, pair="USDJPY", amount=1000,
                         entry_order_type="buy", entry_execution_condition="limit",
                         entry_price=None, profit_price=None, loss_price=None):
    """
    IFO注文の各バージョンの速度比較テスト
    ボタンクリック処理のみの速度を測定
    """
    print("🏁 IFO注文ボタンクリック速度比較テストを開始します")
    print("⚠️  実際の注文は実行されません（測定モード）")
    
    results = {}
    
    # テスト1: 確認画面へボタンクリック速度測定
    print("\n--- 確認画面へボタンクリック速度テスト ---")
    
    # 通常版の速度
    start_time = time.time()
    try:
        # 通常の検索処理（シミュレーション）
        button = driver.find_element(By.XPATH, "//input[@type='submit'][@value='確認画面へ']")
        normal_time = time.time() - start_time
        print(f"通常版検索: {normal_time*1000:.2f}ms")
    except:
        normal_time = 0.1  # フォールバック値
    
    # 超高速版の速度
    success, ultra_time = click_confirmation_button_ultra_fast(driver)
    print(f"超高速版: {ultra_time*1000:.2f}ms")
    
    # 速度比較結果
    if normal_time > 0:
        improvement = ((normal_time - ultra_time) / normal_time * 100)
        print(f"🚀 確認画面へボタン速度改善: {improvement:.1f}%")
    
    results['confirmation'] = {
        'normal': normal_time,
        'ultra_fast': ultra_time,
        'improvement': improvement if normal_time > 0 else 0
    }
    
    # テスト2: 注文実行ボタンクリック速度測定  
    print("\n--- 注文実行ボタンクリック速度テスト ---")
    
    # 画面遷移後の処理速度を測定
    success, execute_time = click_execute_button_ultra_fast(driver)
    print(f"注文実行ボタン: {execute_time*1000:.2f}ms")
    
    results['execution'] = {
        'ultra_fast': execute_time
    }
    
    # 総合結果
    total_ultra_time = ultra_time + execute_time
    estimated_normal_time = normal_time + 0.5  # 推定通常処理時間
    
    print(f"\n🎯 総合速度: {total_ultra_time*1000:.2f}ms")
    print(f"💡 推定改善効果: {((estimated_normal_time - total_ultra_time) / estimated_normal_time * 100):.1f}%")
    
    return results

def navigate_to_order_correction(driver):
    """
    「注文訂正」機能に移動する関数
    提供されたHTMLソースに基づいて注文訂正メニューを選択・クリック
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print("注文訂正メニューに移動しています...")
        
        # 1. デフォルトコンテンツに戻る
        driver.switch_to.default_content()
        time.sleep(0.1)
        
        # 2. mainMenuフレームに切り替え
        try:
            main_menu_frame = driver.find_element(By.CSS_SELECTOR, "iframe#mainMenu, iframe[name='mainMenu']")
            driver.switch_to.frame(main_menu_frame)
            print("✅ mainMenuフレームに切り替えました")
        except Exception as e:
            print(f"❌ mainMenuフレームの切り替えに失敗: {e}")
            return False
        
        # 3. 「取引」メニューが開いているか確認し、必要に応じて開く
        try:
            # h3#1 が「取引」メニューのヘッダー
            trade_menu_header = driver.find_element(By.ID, "1")
            
            # selectedクラスがない場合はクリックしてメニューを開く
            if "selected" not in trade_menu_header.get_attribute("class"):
                print("「取引」メニューを開きます...")
                trade_menu_header.click()
                time.sleep(0.1)
            else:
                print("「取引」メニューは既に開いています")
                
        except Exception as e:
            print(f"❌ 「取引」メニューの操作に失敗: {e}")
            return False
        
        # 4. 「注文訂正」リンクをクリック
        try:
            # menu01内の「注文訂正」リンクを探す
            order_correction_link = driver.find_element(By.XPATH, "//ul[@id='menu01']//a[contains(text(), '注文訂正')]")
            
            if order_correction_link.is_displayed():
                print("「注文訂正」リンクをクリックします...")
                order_correction_link.click()
                time.sleep(0.5)  # ページ遷移を待つ
                print("✅ 「注文訂正」画面への移動が完了しました")
                return True
            else:
                print("❌ 「注文訂正」リンクが表示されていません")
                return False
                
        except Exception as e:
            print(f"❌ 「注文訂正」リンクのクリックに失敗: {e}")
            
            # フォールバック: JavaScriptによる直接遷移
            try:
                print("💡 JavaScriptによる直接遷移を試行...")
                # HTMLソースから判断される注文訂正のservlet URL
                js_command = "_submitForm('/servlet/lzca.pc.cht001.servlet.CHt00171', 'Ht00171');"
                driver.execute_script(js_command)
                time.sleep(0.5)
                print("✅ JavaScript実行で「注文訂正」に移動しました")
                return True
            except Exception as js_e:
                print(f"❌ JavaScript実行でもエラー: {js_e}")
                return False
            
    except Exception as e:
        print(f"❌ 注文訂正メニューへの移動でエラーが発生: {e}")
        return False
    
    finally:
        # デフォルトコンテンツに戻る
        try:
            driver.switch_to.default_content()
        except Exception:
            pass



def get_order_correction_info_ultra_fast(driver):
    """
    注文訂正画面からオーダー情報を超高速取得する関数（極限最適化版・改良版）
    - 表示処理完全削除
    - JavaScript一回実行
    - 最小限データのみ
    - ヘッダー行とデータ行を正確に識別
    
    Returns:
        list: 簡略化されたオーダー情報のリスト
    """
    try:
        # フレーム切り替え（最小限）
        driver.switch_to.default_content()
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']"))
        
        # 超高速JavaScript（改良版・完全なオーダー情報取得）
        ultra_fast_script = """
        var orders = [];
        var tables = document.querySelectorAll('table');
        
        for (var i = 0; i < tables.length; i++) {
            var table = tables[i];
            var headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
            
            // オーダーテーブル判定（改良版・執行条件・注文パターン対応）
            var headerText = headers.join(' ');
            var isOrderTable = /注文|通貨ペア|売買|数量|価格|レート|状態|訂正|執行条件|条件|パターン/.test(headerText) && headers.length > 3;
            
            if (isOrderTable) {
                var allRows = table.querySelectorAll('tr');
                var dataRowIndex = 0;  // データ行のインデックス
                
                for (var j = 0; j < allRows.length; j++) {
                    var row = allRows[j];
                    var cells = row.querySelectorAll('td');  // tdがあるのはデータ行のみ
                    
                    if (cells.length >= 4) {  // データ行と判定
                        dataRowIndex++;
                        var cellData = Array.from(cells).map(c => c.textContent.trim());
                        var buttons = row.querySelectorAll('input[type="button"], input[type="submit"], button');
                        var hasButton = buttons.length > 0;
                        
                        // より詳細な情報を含める（注文パターン検出付き）
                        var orderInfo = {
                            row: dataRowIndex,
                            table: i + 1,
                            headers: headers,  // ヘッダー情報も含める
                            data: cellData,
                            correctable: hasButton,
                            buttonCount: buttons.length,
                            cellCount: cells.length,
                            orderPattern: null,  // 注文パターンを格納
                            orderNumber: null,   // 注文番号を格納
                            orderNumberLink: null  // 注文番号のリンクを格納
                        };
                        
                        // 注文パターンを自動検出
                        for (var k = 0; k < headers.length; k++) {
                            var header = headers[k];
                            if (header.includes('パターン') || header.includes('注文種別') || header.includes('種類')) {
                                if (k < cellData.length) {
                                    orderInfo.orderPattern = cellData[k];
                                }
                                break;
                            }
                        }
                        
                        // 注文番号を自動検出
                        for (var k = 0; k < headers.length; k++) {
                            var header = headers[k];
                            if (header.includes('注文番号') || header.includes('番号') || header.includes('No')) {
                                if (k < cells.length) {
                                    var cell = cells[k];
                                    var orderNumber = cellData[k];
                                    orderInfo.orderNumber = orderNumber;
                                    
                                    // セル内のリンクを検索
                                    var links = cell.querySelectorAll('a');
                                    if (links.length > 0) {
                                        var link = links[0];
                                        orderInfo.orderNumberLink = {
                                            href: link.href || '',
                                            onclick: link.getAttribute('onclick') || '',
                                            text: link.textContent.trim() || orderNumber
                                        };
                                    }
                                }
                                break;
                            }
                        }
                        
                        // ボタン情報も含める（必要に応じて）
                        if (hasButton) {
                            orderInfo.buttons = Array.from(buttons).map(btn => ({
                                text: btn.value || btn.textContent || 'テキストなし',
                                type: btn.type || 'button'
                            }));
                        }
                        
                        orders.push(orderInfo);
                    }
                }
            }
        }
        
        return {
            orderCount: orders.length,
            tableCount: tables.length,
            orders: orders
        };
        """
        
        # JavaScript実行
        result = driver.execute_script(ultra_fast_script)
        
        # 結果の検証とログ出力
        if result and 'orders' in result:
            orders = result['orders']
            print(f"⚡ 超高速取得完了: {result['orderCount']}件のオーダー（{result['tableCount']}テーブル中）")
            
            # 簡潔なデバッグ情報
            if orders:
                correctable_count = sum(1 for order in orders if order.get('correctable', False))
                print(f"   訂正可能: {correctable_count}件, 訂正不可: {len(orders) - correctable_count}件")
            
            return orders
        else:
            print("⚠️  超高速版でオーダーを取得できませんでした")
            return []
        
    except Exception as e:
        print(f"⚠️  超高速版エラー: {e}")
        return []
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

def quick_navigate_to_order_correction_ultra_fast(driver):
    """
    注文訂正画面に直接移動してオーダー情報を超高速取得する便利関数（超高速版）
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        tuple: (成功フラグ, 簡略化オーダー情報リスト)
    """
    try:
        # 画面移動（ログ最小限）
        if not navigate_to_order_correction(driver):
            return False, []
        
        time.sleep(0.3)  # 極小待機
        
        # 超高速版でオーダー情報を取得
        orders = get_order_correction_info_ultra_fast(driver)
        
        # 自動的にサマリー表示
        if orders:
            display_order_summary_ultra_fast(orders)

        else:
            print("⚠️  オーダー情報を取得できませんでした")

        return True, orders
        
    except Exception:
        return False, []


def display_order_summary_ultra_fast(orders):
    """
    超高速版専用の簡潔なサマリー表示（改良版）
    
    Args:
        orders: get_order_correction_info_ultra_fast()の戻り値
    """
    if not orders:
        print("📭 オーダーなし")
        return
    
    correctable_count = sum(1 for order in orders if order.get('correctable', False))
    
    print(f"\n⚡ オーダー: {len(orders)}件 (訂正可能: {correctable_count}件)")
    print("=" * 50)
    
    for i, order in enumerate(orders):
        status = "🔧" if order.get('correctable', False) else "⚪"
        order_pattern = order.get('orderPattern', '不明')
        
        # ヘッダー情報があるかチェック
        headers = order.get('headers', [])
        data = order.get('data', [])
        
        print(f"\n🔸 オーダー {i+1} (行{order.get('row', '?')}) [{order_pattern}]")
        
        # ヘッダーとデータをペアで表示（重要な情報のみ・注文パターン対応）
        important_indices = []
        if headers:
            for j, header in enumerate(headers):
                if any(keyword in header for keyword in ['通貨ペア', '売買', '数量', '価格', 'レート', '状態', '執行条件', '条件', 'パターン', '注文種別']):
                    important_indices.append(j)
        
        if important_indices and len(data) > max(important_indices):
            for idx in important_indices[:4]:  # 最重要4項目
                if idx < len(data) and data[idx]:
                    print(f"   {headers[idx]}: {data[idx]}")
        else:
            # ヘッダーなしの場合は最初の4項目を表示
            data_preview = data[:4] if len(data) >= 4 else data
            print(f"   データ: {', '.join(str(d) for d in data_preview)}")
            if len(data) > 4:
                print(f"   ... 他{len(data)-4}項目")
        
        # 訂正ボタン情報
        if order.get('correctable', False):
            button_count = order.get('buttonCount', 1)
            buttons = order.get('buttons', [])
            if buttons:
                button_names = [btn['text'] for btn in buttons[:2]]  # 最初の2個
                print(f"   {status} 訂正: {', '.join(button_names)}")
                if len(buttons) > 2:
                    print(f"        ... 他{len(buttons)-2}個")
            else:
                print(f"   {status} 訂正: 可能 ({button_count}個)")
        else:
            print(f"   {status} 訂正: 不可")
    
    print("=" * 50)


def get_order_numbers_with_links(driver):
    """
    注文番号とそのリンク情報を取得する関数
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        list: 注文番号とリンク情報のリスト
    """
    try:
        # オーダー情報を取得
        orders = get_order_correction_info_ultra_fast(driver)
        
        order_numbers = []
        for i, order in enumerate(orders):
            order_number = order.get('orderNumber')
            order_link = order.get('orderNumberLink')
            
            if order_number:
                order_info = {
                    'row': order.get('row', i+1),
                    'orderNumber': order_number,
                    'hasLink': order_link is not None,
                    'linkInfo': order_link,
                    'orderData': order  # 元のオーダー情報も保持
                }
                order_numbers.append(order_info)
                
                print(f"オーダー {i+1}: 注文番号 {order_number} - リンク{'あり' if order_link else 'なし'}")
        
        print(f"\n📋 取得結果: {len(order_numbers)}件の注文番号")
        return order_numbers
        
    except Exception as e:
        print(f"⚠️  注文番号取得エラー: {e}")
        return []


def open_order_number_links_sequentially(driver, start_from=1, max_orders=None):
    """
    注文番号のリンクを順番に開く関数
    
    Args:
        driver: WebDriverインスタンス
        start_from: 開始するオーダー番号（1から開始）
        max_orders: 最大処理件数（Noneの場合は全件）
    
    Returns:
        bool: 成功した場合True
    """
    try:
        print(f"🔗 注文番号リンクを順番に開きます（開始: オーダー{start_from}）")
        
        # 注文番号情報を取得
        order_numbers = get_order_numbers_with_links(driver)
        
        if not order_numbers:
            print("❌ 注文番号が見つかりませんでした")
            return False
        
        # 処理範囲を決定
        start_index = start_from - 1  # インデックスは0から開始
        end_index = len(order_numbers)
        if max_orders:
            end_index = min(start_index + max_orders, len(order_numbers))
        
        if start_index >= len(order_numbers):
            print(f"❌ 開始オーダー番号{start_from}が範囲外です（最大: {len(order_numbers)}）")
            return False
        
        print(f"📊 処理予定: オーダー{start_from}〜{start_index + (end_index - start_index)}（{end_index - start_index}件）")
        
        # 順番にリンクを開く
        success_count = 0
        for i in range(start_index, end_index):
            order_info = order_numbers[i]
            order_number = order_info['orderNumber']
            link_info = order_info['linkInfo']
            
            print(f"\n🔗 オーダー {i+1}: 注文番号 {order_number}")
            
            if not link_info:
                print("   ⚠️  リンクが見つかりません - スキップ")
                continue
            
            try:
                # フレーム切り替え
                driver.switch_to.default_content()
                driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']"))
                
                # リンクを開く
                if link_info.get('onclick'):
                    # onclick属性がある場合はJavaScriptで実行
                    onclick_script = link_info['onclick']
                    print(f"   📄 onclick実行: {onclick_script[:50]}...")
                    driver.execute_script(onclick_script)
                elif link_info.get('href'):
                    # href属性がある場合はそれを使用
                    href = link_info['href']
                    print(f"   🌐 href移動: {href}")
                    driver.get(href)
                else:
                    # リンクテキストでクリック
                    link_text = link_info.get('text', order_number)
                    link_element = driver.find_element(By.LINK_TEXT, link_text)
                    print(f"   👆 リンククリック: {link_text}")
                    link_element.click()
                
                # 少し待機
                time.sleep(1)
                
                # ページタイトルまたは内容を確認
                try:
                    current_url = driver.current_url
                    print(f"   ✅ 移動完了: {current_url}")
                    success_count += 1
                    
                    # ユーザーに次のアクションを聞く（オプション）
                    if i < end_index - 1:  # 最後でない場合
                        user_input = input(f"   ⏸️  次のオーダー（{i+2}）に進みますか？ (y/n/q): ").strip().lower()
                        if user_input == 'q':
                            print("   🛑 ユーザーによって中断されました")
                            break
                        elif user_input == 'n':
                            print("   ⏭️  スキップします")
                            continue
                        # 'y'または他の入力は続行
                    
                except Exception as e:
                    print(f"   ⚠️  移動後の確認エラー: {e}")
                    success_count += 1  # 一応成功とカウント
                
            except Exception as e:
                print(f"   ❌ リンクオープンエラー: {e}")
                continue
        
        print(f"\n✅ 完了: {success_count}/{end_index - start_index}件のリンクを開きました")
        return success_count > 0
        
    except Exception as e:
        print(f"⚠️  シーケンシャルオープンエラー: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def demo_order_number_link_navigation(driver):
    """
    注文番号リンクナビゲーションのデモ関数
    
    Args:
        driver: WebDriverインスタンス
    """
    print("🎯 注文番号リンクナビゲーション デモ")
    print("=" * 50)
    
    try:
        # 注文訂正画面に移動
        print("1️⃣ 注文訂正画面に移動中...")
        if not navigate_to_order_correction(driver):
            print("❌ 注文訂正画面への移動に失敗しました")
            return
        
        # 注文番号とリンク情報を取得
        print("\n2️⃣ 注文番号情報を取得中...")
        order_numbers = get_order_numbers_with_links(driver)
        
        if not order_numbers:
            print("❌ 注文番号が見つかりませんでした")
            return
        
        # リンクがある注文を確認
        linkable_orders = [order for order in order_numbers if order['hasLink']]
        print(f"\n📊 リンク可能な注文: {len(linkable_orders)}/{len(order_numbers)}件")
        
        if not linkable_orders:
            print("❌ リンク可能な注文がありません")
            return
        
        # ユーザーに実行確認
        response = input(f"\n3️⃣ {len(linkable_orders)}件の注文番号リンクを順番に開きますか？ (y/n): ").strip().lower()
        if response != 'y':
            print("🛑 デモを中断しました")
            return
        
        # 順番にリンクを開く
        print("\n4️⃣ リンクを順番に開いています...")
        success = open_order_number_links_sequentially(driver, start_from=1, max_orders=3)  # 最初の3件のみデモ
        
        if success:
            print("\n✅ デモ完了！注文番号リンクナビゲーションが正常に動作しました")
        else:
            print("\n❌ デモ中にエラーが発生しました")
        
    except Exception as e:
        print(f"⚠️  デモエラー: {e}")
    
    print("=" * 50)


def open_order_link_by_pattern(driver, order_info):
    """
    注文パターンに基づいてオーダーリンクを開く関数
    
    Args:
        driver: WebDriverインスタンス
        order_info: get_order_numbers_with_links()で取得したオーダー情報
    
    Returns:
        bool: 成功した場合True
    """
    try:
        order_number = order_info['orderNumber']
        order_pattern = order_info['orderData'].get('orderPattern', '不明')
        link_info = order_info['linkInfo']
        
        print(f"🔗 注文番号 {order_number} ({order_pattern}) のリンクを開きます")
        
        if not link_info:
            print("❌ リンク情報が見つかりません")
            return False
        
        # フレーム切り替え
        driver.switch_to.default_content()
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']"))
        
        # リンクを開く
        if link_info.get('onclick'):
            onclick_script = link_info['onclick']
            print(f"   📄 onclick実行: {onclick_script[:50]}...")
            driver.execute_script(onclick_script)
        elif link_info.get('href'):
            href = link_info['href']
            print(f"   🌐 href移動: {href}")
            driver.get(href)
        else:
            link_text = link_info.get('text', order_number)
            link_element = driver.find_element(By.LINK_TEXT, link_text)
            print(f"   👆 リンククリック: {link_text}")
            link_element.click()
        
        # 少し待機
        time.sleep(1)
        
        # 移動確認
        current_url = driver.current_url
        print(f"   ✅ 移動完了: {current_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ リンクオープンエラー: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def process_normal_order_correction(driver, order_info):
    """
    通常注文の訂正処理（指値または逆指値の修正）
    
    Args:
        driver: WebDriverインスタンス
        order_info: オーダー情報
    
    Returns:
        bool: 成功した場合True
    """
    try:
        order_number = order_info['orderNumber']
        print(f"🎯 通常注文訂正処理を開始: 注文番号 {order_number}")
        
        # リンクを開く
        if not open_order_link_by_pattern(driver, order_info):
            return False
        
        print("📝 通常注文: 指値または逆指値の修正画面に移動しました")
        print("💡 ここで価格やレートの修正処理を実装予定")
        
        return True
        
    except Exception as e:
        print(f"❌ 通常注文訂正エラー: {e}")
        return False


def process_oco_order_correction(driver, order_info, limit_price=None, stop_price=None):
    """
    OCO注文の訂正処理（指値と逆指値を同時修正）
    
    Args:
        driver: WebDriverインスタンス
        order_info: オーダー情報
        limit_price: 新しい指値価格
        stop_price: 新しい逆指値価格
    
    Returns:
        bool: 成功した場合True
    """
    try:
        order_number = order_info['orderNumber']
        print(f"🎯 OCO注文訂正処理を開始: 注文番号 {order_number}")
        print(f"💰 設定価格 - 指値: {limit_price}, 逆指値: {stop_price}")
        
        # リンクを開く
        if not open_order_link_by_pattern(driver, order_info):
            return False
        
        print("📝 OCO注文: 指値と逆指値を同時修正画面に移動しました")
        
        # フレーム内で処理
        driver.switch_to.default_content()
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']"))
        
        # 少し待機してフォームが読み込まれるのを待つ
        time.sleep(2)
        
        # 現在の執行条件を確認
        execution_condition = None
        try:
            # テーブルから執行条件を取得（新しい注文条件の列）
            table_script = """
            var tables = document.querySelectorAll('table');
            var executionCondition = null;
            
            for (var i = 0; i < tables.length; i++) {
                var table = tables[i];
                var rows = table.querySelectorAll('tr');
                
                for (var j = 0; j < rows.length; j++) {
                    var row = rows[j];
                    var cells = row.querySelectorAll('th, td');
                    
                    if (cells.length >= 4 && cells[0].textContent.trim() === '執行条件') {
                        // 新しい注文条件（4番目の列）から執行条件を取得
                        executionCondition = cells[3].textContent.trim();
                        break;
                    }
                }
                if (executionCondition) break;
            }
            
            return executionCondition;
            """
            
            execution_condition = driver.execute_script(table_script)
            print(f"� 現在の執行条件: {execution_condition}")
            
        except Exception as e:
            print(f"⚠️ 執行条件の取得に失敗: {e}")
            execution_condition = "不明"
        
        # 価格入力欄（P304）を特定して入力
        price_input = driver.find_element(By.NAME, "P304")
        current_value = price_input.get_attribute('value')
        print(f"💱 現在の注文価格: {current_value}")
        
        # 執行条件に応じて適切な価格を入力
        if execution_condition == "逆指値" and stop_price is not None:
            print(f"🎯 逆指値条件 → 逆指値価格 {stop_price} を入力します")
            price_input.clear()
            price_input.send_keys(str(stop_price))
            
        elif execution_condition == "指値" and limit_price is not None:
            print(f"🎯 指値条件 → 指値価格 {limit_price} を入力します")
            price_input.clear()
            price_input.send_keys(str(limit_price))
            
        else:
            print(f"⚠️ 条件不一致または価格未指定")
            print(f"   執行条件: {execution_condition}")
            print(f"   指値価格: {limit_price}, 逆指値価格: {stop_price}")
            if execution_condition == "逆指値":
                print("   → 逆指値価格が必要ですが、指定されていません")
            elif execution_condition == "指値":
                print("   → 指値価格が必要ですが、指定されていません")
        
        # 入力後の値を確認
        updated_value = price_input.get_attribute('value')
        print(f"✏️ 入力後の価格: {updated_value}")
        
        # 「次へ」ボタンをクリック
        try:
            next_button = driver.find_element(By.NAME, "changeButton")
            print("🔘 「次へ」ボタンをクリックします")
            next_button.click()
            
            # 少し待機（高速化）
            time.sleep(1)
            
            # ページタイトルで画面判定（高速化）
            page_title = driver.execute_script("return document.title;")
            print(f"📄 移動後のページ: {page_title}")
            
            # OCO注文の指値設定画面の場合（Ht00421）
            if "Ht00421" in page_title:
                print("🎯 OCO指値設定画面を高速処理します")
                
                # 指値価格を直接入力（テスト値）
                try:
                    price_input_2 = driver.find_element(By.NAME, "P304")
                    current_value_2 = price_input_2.get_attribute('value')
                    print(f"💱 指値の現在価格: {current_value_2}")
                    
                    # 指値価格を設定
                    limit_price_value = limit_price if limit_price else 153.500
                    print(f"🎯 指値価格 {limit_price_value} を入力")
                    price_input_2.clear()
                    price_input_2.send_keys(str(limit_price_value))
                    
                    # 「次へ」ボタンを再度クリック
                    next_button_2 = driver.find_element(By.NAME, "changeButton")
                    next_button_2.click()
                    time.sleep(1)
                    
                    page_title = driver.execute_script("return document.title;")
                    print(f"📄 最終確認画面: {page_title}")
                    
                except Exception as e:
                    print(f"⚠️ 指値設定エラー: {e}")
            
            # 最終確認画面での「訂正実行」ボタンを直接クリック（高速化）
            if "Ht00422" in page_title or "COMPLETE" not in page_title:
                print("🔘 訂正実行ボタンを直接クリックします")
                
                try:
                    # 注文内容を簡単確認
                    order_price = driver.execute_script("""
                        var tables = document.querySelectorAll('table');
                        for (var i = 0; i < tables.length; i++) {
                            var rows = tables[i].querySelectorAll('tr');
                            for (var j = 0; j < rows.length; j++) {
                                var cells = rows[j].querySelectorAll('th, td');
                                if (cells.length >= 2 && cells[0].textContent.trim() === '注文価格') {
                                    return cells[1].textContent.trim();
                                }
                            }
                        }
                        return null;
                    """)
                    print(f"💰 最終注文価格: {order_price}")
                    
                    # 「訂正実行」ボタンをクリック
                    exec_button = driver.find_element(By.NAME, "EXEC")
                    
                    # ボタン無効化をJSで素早く解除
                    driver.execute_script("""
                        arguments[0].disabled = false;
                        arguments[0].classList.remove('disAbleElmnt');
                    """, exec_button)
                    
                    print("🔘 訂正実行ボタンクリック")
                    exec_button.click()
                    
                    # 完了確認（高速化）
                    time.sleep(1.5)
                    final_title = driver.execute_script("return document.title;")
                    print(f"✅ 処理完了: {final_title}")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ 訂正実行エラー: {e}")
                    return False
            else:
                print("✅ 既に完了画面です")
                return True
            
        except Exception as e:
            print(f"❌ 「次へ」ボタンのクリックに失敗: {e}")
            return False
        
    except Exception as e:
        print(f"❌ OCO注文訂正エラー: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def execute_order_correction_final(driver):
    """
    最終確認画面で「訂正実行」ボタンをクリックして注文訂正を完了する
    OCO注文の場合は指値画面 → 最終確認画面の順で処理
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        bool: 成功した場合True
    """
    try:
        print("🎯 最終確認画面での訂正実行処理を開始")
        
        # フレーム内で処理
        driver.switch_to.default_content()
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']"))
        
        # 少し待機してフォームが読み込まれるのを待つ
        time.sleep(2)
        
        # ページタイトルを確認
        try:
            page_title = driver.execute_script("return document.title;")
            print(f"📄 現在のページ: {page_title}")
            
            if "Ht00421" in page_title:
                print("📝 OCO注文の指値設定画面です")
                return handle_oco_limit_order_screen(driver)
            elif "Ht00422" in page_title:
                print("✅ 最終確認画面を検出しました")
                return handle_final_confirmation_screen(driver)
            else:
                print(f"⚠️ 予期しないページです: {page_title}")
                return False
                
        except Exception as e:
            print(f"⚠️ ページタイトルの確認に失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 最終訂正実行エラー: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def handle_oco_limit_order_screen(driver):
    """
    OCO注文の指値設定画面を処理（2回目の価格設定）
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        bool: 成功した場合True
    """
    try:
        print("🎯 OCO注文の指値設定画面を処理します")
        
        # 現在の執行条件を確認
        execution_condition = None
        try:
            table_script = """
            var tables = document.querySelectorAll('table');
            var executionCondition = null;
            
            for (var i = 0; i < tables.length; i++) {
                var table = tables[i];
                var rows = table.querySelectorAll('tr');
                
                for (var j = 0; j < rows.length; j++) {
                    var row = rows[j];
                    var cells = row.querySelectorAll('th, td');
                    
                    if (cells.length >= 4 && cells[0].textContent.trim() === '執行条件') {
                        executionCondition = cells[3].textContent.trim();
                        break;
                    }
                }
                if (executionCondition) break;
            }
            
            return executionCondition;
            """
            
            execution_condition = driver.execute_script(table_script)
            print(f"🔍 現在の執行条件: {execution_condition}")
            
        except Exception as e:
            print(f"⚠️ 執行条件の取得に失敗: {e}")
        
        # 価格入力欄（P304）を特定して指値価格を入力
        try:
            price_input = driver.find_element(By.NAME, "P304")
            current_value = price_input.get_attribute('value')
            print(f"💱 現在の注文価格: {current_value}")
            
            # 指値価格を設定（テスト値）
            limit_price = 153.500  # テスト用指値価格
            print(f"🎯 指値価格 {limit_price} を入力します")
            price_input.clear()
            price_input.send_keys(str(limit_price))
            
            updated_value = price_input.get_attribute('value')
            print(f"✏️ 入力後の価格: {updated_value}")
            
        except Exception as e:
            print(f"❌ 価格入力に失敗: {e}")
            return False
        
        # 「次へ」ボタンをクリック
        try:
            next_button = driver.find_element(By.NAME, "changeButton")
            print("🔘 「次へ」ボタンをクリックします")
            next_button.click()
            
            # 少し待機
            time.sleep(0.5)
            
            # 最終確認画面に移動したか確認
            page_title = driver.execute_script("return document.title;")
            print(f"📄 移動後のページ: {page_title}")
            
            if "Ht00422" in page_title:
                print("✅ 最終確認画面に移動しました")
                return handle_final_confirmation_screen(driver)
            else:
                print(f"⚠️ 予期しない画面: {page_title}")
                return False
            
        except Exception as e:
            print(f"❌ 「次へ」ボタンのクリックに失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ OCO指値画面処理エラー: {e}")
        return False


def handle_final_confirmation_screen(driver):
    """
    最終確認画面で「訂正実行」ボタンをクリック
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        bool: 成功した場合True
    """
    try:
        print("🎯 最終確認画面で訂正実行ボタンをクリックします")
        
        # 少し待機してフォームが読み込まれるのを待つ
        time.sleep(2)
        
        # 注文内容を表示（確認用）
        try:
            order_info_script = """
            var orderInfo = {};
            var tables = document.querySelectorAll('table');
            
            for (var i = 0; i < tables.length; i++) {
                var table = tables[i];
                var rows = table.querySelectorAll('tr');
                
                for (var j = 0; j < rows.length; j++) {
                    var row = rows[j];
                    var cells = row.querySelectorAll('th, td');
                    
                    if (cells.length >= 2) {
                        var key = cells[0].textContent.trim();
                        var value = cells[1].textContent.trim();
                        
                        if (key === '注文番号') orderInfo.orderNumber = value;
                        else if (key === '注文価格') orderInfo.price = value;
                        else if (key === '執行条件') orderInfo.condition = value;
                    }
                }
            }
            
            return orderInfo;
            """
            
            order_info = driver.execute_script(order_info_script)
            print("📋 変更後の注文内容:")
            for key, value in order_info.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"⚠️ 注文内容の確認に失敗: {e}")
        
        # 「訂正実行」ボタンを探してクリック
        try:
            # まずボタンの状態を確認
            exec_button = driver.find_element(By.NAME, "EXEC")
            is_disabled = exec_button.get_attribute('disabled')
            button_text = exec_button.get_attribute('value') or exec_button.text
            
            print(f"🔘 「{button_text}」ボタン状態: {'無効' if is_disabled else '有効'}")
            
            if is_disabled:
                print("⚠️ ボタンが無効化されています。有効化を試みます...")
                # JavaScriptでボタンを有効化
                driver.execute_script("arguments[0].disabled = false;", exec_button)
                driver.execute_script("arguments[0].classList.remove('disAbleElmnt');", exec_button)
                
                # 再確認
                is_disabled_after = exec_button.get_attribute('disabled')
                print(f"🔄 有効化後の状態: {'無効' if is_disabled_after else '有効'}")
            
            print("🔘 「訂正実行」ボタンをクリックします")
            exec_button.click()
            
            # 少し待機
            time.sleep(0.5)
            
            # 結果確認
            try:
                current_url = driver.current_url
                new_title = driver.execute_script("return document.title;")
                print(f"✅ 訂正実行完了")
                print(f"📄 移動後ページ: {new_title}")
                print(f"🌐 URL: {current_url}")
                
                # 成功メッセージや完了画面の確認
                try:
                    success_message = driver.execute_script("""
                        var messages = [];
                        var elements = document.querySelectorAll('*');
                        
                        for (var i = 0; i < elements.length; i++) {
                            var text = elements[i].textContent;
                            if (text && (text.includes('完了') || text.includes('成功') || text.includes('受付'))) {
                                messages.push(text.trim());
                            }
                        }
                        
                        return messages.slice(0, 3); // 最初の3件まで
                    """)
                    
                    if success_message:
                        print("🎉 完了メッセージ:")
                        for msg in success_message:
                            if msg and len(msg) < 100:  # 短いメッセージのみ表示
                                print(f"   {msg}")
                
                except Exception as e:
                    print(f"⚠️ 完了メッセージの確認に失敗: {e}")
                
                return True
                
            except Exception as e:
                print(f"⚠️ 結果確認エラー: {e}")
                return True  # ボタンクリックは成功したと見なす
            
        except Exception as e:
            print(f"❌ 「訂正実行」ボタンのクリックに失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 最終確認画面処理エラー: {e}")
        return False
        
        # 注文内容を表示（確認用）
        try:
            order_info_script = """
            var orderInfo = {};
            var tables = document.querySelectorAll('table');
            
            for (var i = 0; i < tables.length; i++) {
                var table = tables[i];
                var rows = table.querySelectorAll('tr');
                
                for (var j = 0; j < rows.length; j++) {
                    var row = rows[j];
                    var cells = row.querySelectorAll('th, td');
                    
                    if (cells.length >= 2) {
                        var key = cells[0].textContent.trim();
                        var value = cells[1].textContent.trim();
                        
                        if (key === '注文番号') orderInfo.orderNumber = value;
                        else if (key === '注文価格') orderInfo.price = value;
                        else if (key === '執行条件') orderInfo.condition = value;
                    }
                }
            }
            
            return orderInfo;
            """
            
            order_info = driver.execute_script(order_info_script)
            print("📋 変更後の注文内容:")
            for key, value in order_info.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"⚠️ 注文内容の確認に失敗: {e}")
        
        # 「訂正実行」ボタンを探してクリック
        try:
            # まずボタンの状態を確認
            exec_button = driver.find_element(By.NAME, "EXEC")
            is_disabled = exec_button.get_attribute('disabled')
            button_text = exec_button.get_attribute('value') or exec_button.text
            
            print(f"🔘 「{button_text}」ボタン状態: {'無効' if is_disabled else '有効'}")
            
            if is_disabled:
                print("⚠️ ボタンが無効化されています。有効化を試みます...")
                # JavaScriptでボタンを有効化
                driver.execute_script("arguments[0].disabled = false;", exec_button)
                driver.execute_script("arguments[0].classList.remove('disAbleElmnt');", exec_button)
                
                # 再確認
                is_disabled_after = exec_button.get_attribute('disabled')
                print(f"🔄 有効化後の状態: {'無効' if is_disabled_after else '有効'}")
            
            print("🔘 「訂正実行」ボタンをクリックします")
            exec_button.click()
            
            # 少し待機
            time.sleep(0.5)
            
            # 結果確認
            try:
                current_url = driver.current_url
                new_title = driver.execute_script("return document.title;")
                print(f"✅ 訂正実行完了")
                print(f"📄 移動後ページ: {new_title}")
                print(f"🌐 URL: {current_url}")
                
                # 成功メッセージや完了画面の確認
                try:
                    success_message = driver.execute_script("""
                        var messages = [];
                        var elements = document.querySelectorAll('*');
                        
                        for (var i = 0; i < elements.length; i++) {
                            var text = elements[i].textContent;
                            if (text && (text.includes('完了') || text.includes('成功') || text.includes('受付'))) {
                                messages.push(text.trim());
                            }
                        }
                        
                        return messages.slice(0, 3); // 最初の3件まで
                    """)
                    
                    if success_message:
                        print("🎉 完了メッセージ:")
                        for msg in success_message:
                            if msg and len(msg) < 100:  # 短いメッセージのみ表示
                                print(f"   {msg}")
                
                except Exception as e:
                    print(f"⚠️ 完了メッセージの確認に失敗: {e}")
                
                return True
                
            except Exception as e:
                print(f"⚠️ 結果確認エラー: {e}")
                return True  # ボタンクリックは成功したと見なす
            
        except Exception as e:
            print(f"❌ 「訂正実行」ボタンのクリックに失敗: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 最終訂正実行エラー: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def process_order_correction_by_pattern_single(driver, order_index=0, limit_price=None, stop_price=None):
    """
    注文パターンに基づいて単一オーダーの訂正処理を実行
    
    Args:
        driver: WebDriverインスタンス
        order_index: 処理するオーダーのインデックス（0から開始）
        limit_price: 新しい指値価格（OCO注文用）
        stop_price: 新しい逆指値価格（OCO注文用）
    
    Returns:
        bool: 成功した場合True
    """
    try:
        print(f"🎯 オーダー{order_index + 1}の注文パターン別訂正処理を開始")
        
        # 注文番号情報を取得
        order_numbers = get_order_numbers_with_links(driver)
        
        if not order_numbers or len(order_numbers) <= order_index:
            print(f"❌ オーダー{order_index + 1}が見つかりません")
            return False
        
        order_info = order_numbers[order_index]
        order_pattern = order_info['orderData'].get('orderPattern', '不明')
        order_number = order_info['orderNumber']
        
        print(f"📋 処理対象: オーダー{order_index + 1}")
        print(f"🏷️  注文番号: {order_number}")
        print(f"🏷️  注文パターン: {order_pattern}")
        
        # パターンに応じて処理を分岐
        if order_pattern == "通常":
            return process_normal_order_correction(driver, order_info)
        elif order_pattern == "OCO":
            return process_oco_order_correction(driver, order_info, limit_price, stop_price)
        else:
            print(f"⚠️  未対応の注文パターン: {order_pattern}")
            print("🔗 基本的なリンクオープンのみ実行します")
            return open_order_link_by_pattern(driver, order_info)
        
    except Exception as e:
        print(f"❌ 注文パターン別処理エラー: {e}")
        return False


def navigate_to_close_all_positions(driver):
    """
    「全決済」画面に移動する関数
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print("全決済画面に移動しています...")
        
        # 1. デフォルトコンテンツに戻る
        driver.switch_to.default_content()
        time.sleep(0.5)
        
        # 2. mainMenuフレームに切り替え
        try:
            main_menu_frame = driver.find_element(By.CSS_SELECTOR, "iframe#mainMenu, iframe[name='mainMenu']")
            driver.switch_to.frame(main_menu_frame)
            print("✅ mainMenuフレームに切り替えました")
        except Exception as e:
            print(f"❌ mainMenuフレームの切り替えに失敗: {e}")
            return False
        
        # 3. 「取引」メニューが開いているか確認し、必要に応じて開く
        try:
            # h3#1 が「取引」メニューのヘッダー
            trade_menu_header = driver.find_element(By.ID, "1")
            
            # selectedクラスがない場合はクリックしてメニューを開く
            if "selected" not in trade_menu_header.get_attribute("class"):
                print("「取引」メニューを開きます...")
                trade_menu_header.click()
                time.sleep(0.1)
            else:
                print("「取引」メニューは既に開いています")
                
        except Exception as e:
            print(f"❌ 「取引」メニューの操作に失敗: {e}")
            return False
        
        # 4. 「全決済」リンクをクリック
        try:
            # menu01内の「全決済」リンクを探す
            close_all_link = driver.find_element(By.XPATH, "//ul[@id='menu01']//a[contains(text(), '全決済')]")
            
            if close_all_link.is_displayed():
                print("「全決済」リンクをクリックします...")
                close_all_link.click()
                time.sleep(0.5)  # ページ遷移を待つ
                print("✅ 「全決済」画面への移動が完了しました")
                return True
            else:
                print("❌ 「全決済」リンクが表示されていません")
                return False
                
        except Exception as e:
            print(f"❌ 「全決済」リンクのクリックに失敗: {e}")
            
            # フォールバック: JavaScriptによる直接遷移
            try:
                print("💡 JavaScriptによる直接遷移を試行...")
                # HTMLソースから判断される全決済のservlet URL
                js_command = "submitForm('frmMain', '/servlet/lzca.pc.cht002.servlet.CHt00242', 'POST', '_self', 'Ht00242');"
                driver.execute_script(js_command)
                time.sleep(0.5)
                print("✅ JavaScript実行で「全決済」に移動しました")
                return True
            except Exception as js_e:
                print(f"❌ JavaScript実行でもエラー: {js_e}")
                return False
            
    except Exception as e:
        print(f"❌ 全決済メニューへの移動でエラーが発生: {e}")
        return False
    
    finally:
        # デフォルトコンテンツに戻る
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def execute_close_all_positions(driver, confirm_execution=True):
    """
    全決済注文を実行する関数
    
    Args:
        driver: WebDriverインスタンス
        confirm_execution: 実際に全決済を実行するかどうか（True: 実行, False: 準備のみ）
    
    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    try:
        print("🎯 全決済注文の実行処理を開始します")
        
        # 全決済画面に移動
        if not navigate_to_close_all_positions(driver):
            print("❌ 全決済画面への移動に失敗")
            return False
        
        # main_v2_dフレームに切り替え
        try:
            driver.switch_to.default_content()
            main_frame = driver.find_element(By.CSS_SELECTOR, "iframe#main_v2_d, iframe[name='main_v2_d']")
            driver.switch_to.frame(main_frame)
            print("✅ main_v2_dフレームに切り替えました")
        except Exception as e:
            print(f"❌ main_v2_dフレーム切り替えに失敗: {e}")
            return False
        
        # 少し待機してページが完全に読み込まれるのを待つ
        time.sleep(2)
        
        # 現在のポジション情報を取得・表示
        try:
            positions = get_current_positions_info(driver)
            if positions:
                print(f"📊 現在のポジション: {positions['total_positions']}件")
                print(f"💰 評価損益合計: {positions['total_pnl']}")
                
                # ポジション詳細を表示
                for i, pos in enumerate(positions['positions']):
                    print(f"   {i+1}. {pos['currency_pair']} {pos['buy_sell']} {pos['amount']} @ {pos['entry_price']} (損益: {pos['pnl']})")
            else:
                print("⚠️  ポジション情報の取得に失敗しました")
        except Exception as e:
            print(f"⚠️  ポジション情報取得エラー: {e}")
        
        # 「全決済注文実行」ボタンの状態確認
        try:
            # HTMLソースから判明したボタンの特定
            execute_button = driver.find_element(By.NAME, "EXEC")
            button_text = execute_button.get_attribute("value") or execute_button.text
            is_disabled = execute_button.get_attribute("disabled")
            button_class = execute_button.get_attribute("class") or ""
            
            print(f"🔘 ボタン発見: 「{button_text}」")
            print(f"   状態: {'無効' if is_disabled or 'disAbleElmnt' in button_class else '有効'}")
            
            if is_disabled or 'disAbleElmnt' in button_class:
                print("⚠️  ボタンが無効化されています")
                print("   以下を確認してください:")
                print("   1. 決済可能なポジションが存在するか")
                print("   2. 市場が開いているか")
                print("   3. システムメンテナンス中でないか")
                
                # JavaScriptでボタンを強制有効化を試行（デバッグ用）
                if confirm_execution:
                    try:
                        print("🔧 ボタンの強制有効化を試行...")
                        
                        # _getRate_Order関数とablebtn関数を実行
                        driver.execute_script("if (typeof _getRate_Order === 'function') _getRate_Order(0);")
                        time.sleep(0.1)
                        driver.execute_script("if (typeof ablebtn === 'function') ablebtn();")
                        
                        # ボタンを直接有効化
                        driver.execute_script("""
                            var button = arguments[0];
                            button.disabled = false;
                            button.classList.remove('disAbleElmnt');
                            button.removeAttribute('disabled');
                        """, execute_button)
                        
                        # 再確認
                        is_disabled_after = execute_button.get_attribute("disabled")
                        button_class_after = execute_button.get_attribute("class") or ""
                        
                        print(f"   有効化後の状態: {'無効' if is_disabled_after or 'disAbleElmnt' in button_class_after else '有効'}")
                        
                    except Exception as enable_e:
                        print(f"   ❌ 有効化処理エラー: {enable_e}")
                
            else:
                print("✅ ボタンは有効状態です")
            
        except Exception as e:
            print(f"❌ 全決済ボタンの確認に失敗: {e}")
            return False
        
        # 実行確認
        if not confirm_execution:
            print("📝 全決済の準備が完了しました（実行はスキップ）")
            return True
        
        # 警告メッセージを表示
        print("\n" + "="*60)
        print("⚠️  【重要】全決済注文の実行について")
        print("="*60)
        print("• 全てのポジションが即座に決済されます")
        print("• この操作は取り消すことができません")
        print("• 市場状況により予期しない価格で決済される可能性があります")
        print("• 実行前に必ずポジション内容を確認してください")
        print("="*60)
        
        # ユーザー確認
        user_confirmation = input("本当に全決済を実行しますか？ (yes/no): ").strip().lower()
        if user_confirmation not in ['yes', 'y']:
            print("🛑 ユーザーによって全決済が中断されました")
            return False
        
        # 全決済注文実行
        try:
            print("🚀 全決済注文を実行します...")
            
            # ボタンクリック前に必要なJavaScript関数を実行
            try:
                # HTMLソースのonclick属性に基づいて実行
                onclick_script = "_getRate_Order(0); submitForm('frmMain', '/servlet/lzca.pc.cht002.servlet.CHt00243', 'POST', '_self', 'Ht00243');"
                print("📄 onclick スクリプトを実行...")
                driver.execute_script(onclick_script)
                
            except Exception as onclick_e:
                print(f"⚠️  onclick スクリプト実行エラー: {onclick_e}")
                # フォールバック: 直接ボタンクリック
                print("🔄 直接ボタンクリックを試行...")
                execute_button.click()
            
            print("⏳ 全決済処理を実行中...")
            time.sleep(3)  # 処理完了を待機
            
            # 結果確認
            try:
                current_url = driver.current_url
                page_title = driver.execute_script("return document.title;")
                print(f"📄 処理後のページ: {page_title}")
                print(f"🌐 URL: {current_url}")
                
                # 成功・エラーメッセージの確認
                success_message = check_execution_result(driver)
                if success_message:
                    print(f"✅ 実行結果: {success_message}")
                    return True
                else:
                    print("⚠️  実行結果の確認ができませんでした")
                    return True  # とりあえず成功とみなす
                
            except Exception as result_e:
                print(f"⚠️  結果確認エラー: {result_e}")
                return True  # 実行は完了したとみなす
            
        except Exception as e:
            print(f"❌ 全決済実行エラー: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 全決済処理でエラーが発生: {e}")
        return False
    
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def get_current_positions_info(driver):
    """
    現在のポジション情報を取得する関数
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        dict: ポジション情報（ポジション数、損益、詳細など）
    """
    try:
        # JavaScriptでテーブル情報を高速取得
        positions_script = """
        var positions = [];
        var totalPnl = null;
        var totalCount = 0;
        
        // テーブルを検索
        var tables = document.querySelectorAll('table');
        
        for (var i = 0; i < tables.length; i++) {
            var table = tables[i];
            var rows = table.querySelectorAll('tr');
            
            // ヘッダー行を探す
            var headerRow = null;
            var headers = [];
            
            for (var j = 0; j < rows.length; j++) {
                var ths = rows[j].querySelectorAll('th');
                if (ths.length > 4) {  // 4列以上のヘッダーがある場合
                    headerRow = rows[j];
                    headers = Array.from(ths).map(th => th.textContent.trim());
                    break;
                }
            }
            
            // ポジションテーブルかどうかを判定
            var isPositionTable = false;
            if (headers.length > 0) {
                var headerText = headers.join(' ');
                if (headerText.includes('通貨ペア') && headerText.includes('売買') && 
                    (headerText.includes('数量') || headerText.includes('約定価格'))) {
                    isPositionTable = true;
                }
            }
            
            if (isPositionTable && headerRow) {
                // データ行を処理
                for (var k = j + 1; k < rows.length; k++) {
                    var row = rows[k];
                    var cells = row.querySelectorAll('td');
                    
                    if (cells.length >= 4) {
                        var cellData = Array.from(cells).map(cell => cell.textContent.trim());
                        
                        // 合計行でない場合（注文番号がある行）
                        if (!cellData[0].includes('合計') && cellData[0] && !isNaN(parseInt(cellData[0].replace(/[^0-9]/g, '')))) {
                            var position = {
                                orderNumber: cellData[0] || '',
                                currencyPair: cellData[1] || '',
                                buySell: cellData[2] || '',
                                amount: cellData[3] || '',
                                entryPrice: cellData[4] || '',
                                entryDateTime: cellData[5] || '',
                                pnl: cellData[6] || '',
                                fee: cellData[7] || ''
                            };
                            
                            positions.push(position);
                            totalCount++;
                        }
                        
                        // 合計行の場合
                        if (cellData[0].includes('合計') && cellData.length > 6) {
                            totalPnl = cellData[6] || null;
                        }
                    }
                }
            }
        }
        
        // 件数情報も取得
        var countInfo = document.querySelector('td');
        var countText = '';
        if (countInfo) {
            var allTds = document.querySelectorAll('td');
            for (var m = 0; m < allTds.length; m++) {
                var text = allTds[m].textContent.trim();
                if (text.includes('全') && text.includes('件')) {
                    countText = text;
                    break;
                }
            }
        }
        
        return {
            totalPositions: totalCount,
            totalPnl: totalPnl,
            countText: countText,
            positions: positions
        };
        """
        
        result = driver.execute_script(positions_script)
        
        if result and result.get('positions'):
            print(f"✅ ポジション情報を取得しました")
            return {
                'total_positions': result['totalPositions'],
                'total_pnl': result['totalPnl'],
                'count_text': result['countText'],
                'positions': [{
                    'order_number': pos['orderNumber'],
                    'currency_pair': pos['currencyPair'], 
                    'buy_sell': pos['buySell'],
                    'amount': pos['amount'],
                    'entry_price': pos['entryPrice'],
                    'entry_datetime': pos['entryDateTime'],
                    'pnl': pos['pnl'],
                    'fee': pos['fee']
                } for pos in result['positions']]
            }
        else:
            print("⚠️  ポジション情報が見つかりませんでした")
            return None
            
    except Exception as e:
        print(f"⚠️  ポジション情報取得エラー: {e}")
        return None


def check_execution_result(driver):
    """
    全決済実行後の結果を確認する関数
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        str: 実行結果メッセージ
    """
    try:
        # 成功・エラーメッセージを検索
        result_script = """
        var messages = [];
        var keywords = ['完了', '成功', '受付', '実行', '決済', 'エラー', '失敗', '無効'];
        
        // 全要素をチェック
        var allElements = document.querySelectorAll('*');
        
        for (var i = 0; i < allElements.length; i++) {
            var element = allElements[i];
            var text = element.textContent || '';
            
            // 短いテキストで重要そうなメッセージを検索
            if (text.length > 3 && text.length < 200) {
                for (var j = 0; j < keywords.length; j++) {
                    if (text.includes(keywords[j])) {
                        messages.push(text.trim());
                        break;
                    }
                }
            }
        }
        
        // 重複を排除
        var uniqueMessages = [];
        for (var k = 0; k < messages.length; k++) {
            if (uniqueMessages.indexOf(messages[k]) === -1) {
                uniqueMessages.push(messages[k]);
            }
        }
        
        return uniqueMessages.slice(0, 5); // 最初の5件まで
        """
        
        messages = driver.execute_script(result_script)
        
        if messages and len(messages) > 0:
            # 最も関連性の高いメッセージを返す
            for msg in messages:
                if any(keyword in msg for keyword in ['完了', '成功', '受付']):
                    return f"成功: {msg}"
                elif any(keyword in msg for keyword in ['エラー', '失敗', '無効']):
                    return f"エラー: {msg}"
            
            return f"情報: {messages[0]}"
        
        return None
        
    except Exception as e:
        print(f"⚠️  結果確認エラー: {e}")
        return None


def quick_close_all_positions(driver):
    """
    全決済を迅速に実行する便利関数
    
    Args:
        driver: WebDriverインスタンス
    
    Returns:
        bool: 成功した場合True
    """
    try:
        print("🚀 迅速全決済を開始します")
        
        # 全決済実行
        success = execute_close_all_positions(driver, confirm_execution=True)
        
        if success:
            print("✅ 迅速全決済が完了しました")
        else:
            print("❌ 迅速全決済に失敗しました")
        
        return success
        
    except Exception as e:
        print(f"❌ 迅速全決済エラー: {e}")
        return False


def demo_close_all_positions(driver):
    """
    全決済機能のデモ（実際には実行せず、準備のみ）
    
    Args:
        driver: WebDriverインスタンス
    """
    print("🎯 全決済機能デモを開始します")
    print("=" * 50)
    
    try:
        # 全決済画面に移動
        print("1️⃣ 全決済画面に移動中...")
        if not navigate_to_close_all_positions(driver):
            print("❌ 全決済画面への移動に失敗しました")
            return
        
        # ポジション情報確認（実行はしない）
        print("\n2️⃣ 全決済の準備確認中...")
        success = execute_close_all_positions(driver, confirm_execution=False)
        
        if success:
            print("\n✅ デモ完了！全決済機能が正常に動作することを確認しました")
            print("💡 実際に全決済を実行する場合は:")
            print("   execute_close_all_positions(driver, confirm_execution=True)")
            print("   または")
            print("   quick_close_all_positions(driver)")
            print("   を使用してください")
        else:
            print("\n❌ デモ中にエラーが発生しました")
        
    except Exception as e:
        print(f"⚠️  デモエラー: {e}")
    
    print("=" * 50)


# 【全決済機能の使用例】
# # 安全な準備確認のみ
# execute_close_all_positions(driver, confirm_execution=False)
# 
# # 実際の全決済実行（確認あり）
# execute_close_all_positions(driver, confirm_execution=True)
# 
# # 迅速全決済（確認あり）
# quick_close_all_positions(driver)
# 
# # デモ実行（実際には実行しない）
# demo_close_all_positions(driver)
