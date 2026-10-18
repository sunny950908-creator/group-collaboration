# Group Final Report

本文件為 G01 的最終候選報告，使用繁體中文撰寫。狀態：等待實際操作者閱讀並明確確認，尚未宣告正式結案。候選報告準備日期：2026-10-19（Asia/Taipei）。

## Assignment

依據 `specs/00_group_collaboration_assignment.md` 至 `specs/07_testing_and_finalization.md` 八份教授規格，完成不依賴 Dispatcher 的小組協作第一層：以 Git 管理版本、GitHub 保存共享資料，讓人類與各自的本機 AI 透過標準化命令及事件協作。

群組為 G01；作業入口為 `.group/assignment/assignment.md`。共享儲存庫為 https://github.com/sunny950908-creator/group-collaboration ，canonical branch 為 `main`。

## Result

已完成 Python 標準函式庫實作的 `groupctl.py`，提供身分與群組設定、遠端事件探索、安全同步、發布、審查事件、精確提交整合、隔離快照測試與分階段結案功能。事件依 protocol 0.1 儲存為獨立 JSON，發布後不修改；個人功能分支與 canonical 接受狀態分開管理。

已完成可攜式 AI 操作說明 `AGENT_INSTRUCTIONS.md`，定義 SYNC、PUB、INT、REV、TEST、STATUS、FINAL 的程序、安全界線與證據要求。Git 與 groupctl 負責可重現的機械操作，本機 AI 負責 diff、介面假設、衝突意圖及語意相容性判斷；不以 Git 合併成功代替程式正確性。

測試包含 `tests/test_workflow.py` 的真實 Git 流程及安全性案例，以及 `tests/test_event_validation.py` 的協定與錯誤輸入案例。`demo.py` 保留可重現的本機示範能力；本報告沒有沿用它的舊結案產物。

本次課程示範由一位實際操作者管理三份獨立 clone、三個本機 AI 對話，以 P17、P22、P31 三個身分及個人分支，實際向同一個 GitHub 儲存庫發布、抓取、審查與整合。各身分的資訊透過遠端分支與事件發現；目前這份 clone 的操作身分始終為 P22。已接受成果已正式納入並推送 main。

## Canonical Commit

- 正式納入三個模擬身分成果的 main merge commit：`f4a80d5a34699d5f5c50b0391b926f97fb9d6f92`。
- 本次 FINAL 鎖定的 canonical commit：`88754814b70f77ff21cbcdb324d516cab7f7957c`。
- 本次最終驗證所測的 commit：`88754814b70f77ff21cbcdb324d516cab7f7957c`，與鎖定的 canonical commit 完全相同。
- 最終測試事件：`E-20261018T162229Z-P22-ba0a6ce30f9e`。
- 候選事件：`E-20261018T162233Z-P22-e8e1f6f6b01e`；報告位置：`.group/final/candidate.md`。

FINAL 準備程序後新增的測試事件、候選事件及報告提交屬結案中繼資料，與被測來源提交不同。不能把後續 main HEAD 的雜湊說成已被上述測試精確測過，也不能把祖先測試當成 HEAD 的精確證據。程式或設定若再修改，或遠端狀態改變，須依規格重新核對，必要時重新準備。

## Important Changes

### 已接受的獨立貢獻

| 模擬身分 | 已發布 change_id | 內容 |
| --- | --- | --- |
| P17 | `C-P17-a1479e680585` | 強化事件型別驗證及診斷；新增協定相容性與錯誤輸入測試。 |
| P22 | `C-P22-c33929e7e475` | STATUS 新增精確 HEAD 測試證據篩選、回歸測試及繁體中文文件。 |
| P22 | `C-P22-3e292ade8030` | 說明人類／本機 AI 協作分工的 docstring，並將檢查命令上限調整為 300 秒。 |
| P31 | `C-P31-97f9804a1573` | 說明執行需求與 GitHub 共享資料用途的 docstring，提供刻意衝突案例。 |

四項發布提交都已由 Git 歷史確認納入 canonical main，沒有以尚未推送的私人目錄代替小組成果。

### 事件驗證與 STATUS 證據

P17 的 `validate()` 檢查事件物件、必填文字欄位、字串陣列元素、時間戳記與 integration verification 值；錯誤輸入提供明確的 `Error`。保留既有欄位名稱與事件語意，不增加協定版本；選用擴充仍受支援，`test_evidence` 元素因協定未規定格式而保留彈性。

P22 保留 STATUS 原有 `test_results`，新增 `current_commit_test_results`，僅收錄事件 `commit` 與目前 HEAD 完全一致的已發布 `test_result`。沒有符合證據時回傳空陣列；不同提交或祖先提交不能混用。這是 CLI 輸出擴充，沒有改動事件協定。限制與範例記錄於 `docs/STATUS_ZH_TW.md`。

### 120 秒逾時與 300 秒修正

原本每項檢查命令限制 120 秒；P22 發布紀錄記載先前 PUB 因此逾時，而直接執行同一組 17 個測試曾以 137.333 秒通過。增加 Git clone、merge、測試及結案流程的端對端測試，在該 Windows 環境可能超過舊上限，不能把環境耗時誤判為產品測試失敗。

提交 `6d5afb3ec9f52bbf85e1847b0d01353c618d4ee7` 將 `Repo.checks()` 每個命令上限改為 300 秒，並同步 README 與 AI 操作說明。修正後 PUB 的已發布證據顯示 17 個測試於 139.900 秒通過。沒有刪除測試、跳過案例或修改預期值；真正逾時仍回報 partial，非零退出仍回報 fail。

### 正常合併、刻意衝突與解決

1. P17 發布事件為 `E-20261016T075535Z-P17-89358cfc363b`。P22 檢查實際 diff 並測試精確發布提交，發布 accept 審查 `E-20261016T081632Z-P22-d4696b3c5edd`。將 P17 的 `486931d079fb9c170ec4f37a39e67bca58c343e1` 正常合入 P22，無文字衝突；merge commit 為 `a2199ff0ea6a64bd6525cc37619b660e059f5fc8`，整合事件為 `E-20261016T082120Z-P22-57150afbfb1a`，合併快照的 17 個測試通過。
2. P22 與 P31 刻意修改 `groupctl.py` 同一行模組 docstring。P22 發布事件為 `E-20261016T084812Z-P22-166547bb7bf8`；P31 發布事件為 `E-20261016T083035Z-P31-4a6e234026c3`。整合 P31 的 `f83cfc8112f57a54a928174237632dbf71cbae89` 時發生真實 Git 衝突。
3. 解衝突時檢查基底及雙方意圖，將 P22 的「學生與本機 AI 透過 Git 協作、AI 判斷／工具機械操作分工」與 P31 的「GitHub 保存共享協作資料」合併，同時保留 protocol 0.1、Python 3.10+、Git 需求，以及無須 API 整合或自訂伺服器的說明，沒有任意選擇 ours／theirs。
4. 解衝突提交為 `5cd62dcf8cdb15e31efeb5f37dfa7387d653eb1f`；成功整合事件為 `E-20261016T085350Z-P22-5618d4573116`。docstring 以外程式保留既有驗證、STATUS 篩選與 300 秒設定；解決後 17 個測試於 137.418 秒通過。
5. 接受整合成果時先安全更新本機 main，再以 merge 策略納入 P22 分支，未 force-push、未丟棄他人工作。main 的 `f4a80d5` 經完整驗證後，發布測試事件 `E-20261018T161840Z-P22-9a89c81fa66a`，17 個測試通過。

## Validation

本次 FINAL 由 P22 在乾淨、與 origin/main 一致的 main 啟動；先 fetch 並探索所有遠端分支事件，再對鎖定的 canonical commit 執行 `groupctl final-prepare`。最終驗證在隔離的 detached worktree 執行，不以其他版本測試取代。

環境：Windows、Python 3.14.3、Git 2.55.0.windows.3。執行命令如下；`python` 為本次 groupctl 使用的相同直譯器：

```text
python -m py_compile groupctl.py demo.py
python -m unittest discover -s tests -v
```

實際結果：

| 項目 | 結果 |
| --- | --- |
| 編譯檢查 | exit code 0，通過。 |
| unittest | exit code 0，17 個測試全部通過，61.930 秒。 |
| groupctl 統計 | passed=2、failed=0、skipped=0；單位為檢查命令，不是單元測試案例。 |
| automated_result | pass。 |
| 被測提交 | `88754814b70f77ff21cbcdb324d516cab7f7957c`。 |
| 證據事件 | `E-20261018T162229Z-P22-ba0a6ce30f9e`。 |

測試覆蓋協定範例、必填欄位與錯誤型別、時間戳記、選用擴充、正常整合、真實 Git 衝突處理、髒工作目錄保護、review 不自動合併、STATUS 精確提交證據、無檢查不得宣稱通過、秘密檔案拒絕、未整合改動阻止結案，以及候選後修改程式使驗證失效等行為。

`test_semantic_incompatibility_despite_clean_merge` 以 producer 回傳字典、consumer 仍呼叫字串 `upper()` 重現「文字可合併但行為不相容」；案例要求 Git 合併成功，隨後測試與語意判定必須記錄失敗。此案例的預期產品失敗由測試成功檢出，所以整體測試結果為通過。

額外核對已確認四項發布提交均納入、無殘留衝突標記、所有探索到的事件可通過驗證，並檢查 STATUS 新欄位、300 秒上限、合併後 docstring 及 CLI help。語意審查確認 P17 型別檢查與 P22 的 commit 篩選介面相容，未以 Git 合併或測試單獨代替語意判斷。

設定的 `human_checks_required` 為空，未假報已完成額外人工測試。實際操作者仍須閱讀本候選報告，確認成果、限制及身分標示；目前尚未取得此次結案的人類確認。

## Known Limitations

- 本次是一位實際操作者模擬三個成員身分，不是三位真人獨立操作；三份 clone、三個本機 AI 對話與真正 GitHub 操作不能證明三位真人的獨立協作。
- GitHub 示範實際完成正常合併與刻意 docstring 衝突；「無文字衝突但行為不相容」由自動化測試在臨時本機 Git 儲存庫重現，未在本次 GitHub 功能分支另做同一案例。
- 自動化測試中的三人流程、衝突修復及確認動作是腳本模擬，只證明流程機制；不等同此次實際使用者的人類確認。
- 型別驗證不證明事件聲明真實。`test_evidence` 只保留陣列要求，不強加未定義的元素格式；系統假設可信組員，不提供安全認證或防惡意改寫歷史機制。
- STATUS 的精確證據不涵蓋未提交修改；發布事件或只改文件也會形成新提交，因此 `current_commit_test_results` 可能為空。空陣列不表示測試失敗，非空也不代表全部通過。
- 300 秒為每個檢查命令的上限，不保證任何環境都足夠。測試通過不能證明沒有所有可能錯誤；本次沒有完整跨平台環境矩陣、GUI 或負載測試。
- README 與 `docs/GITHUB_DEMO.md` 保留初版的「未連 GitHub／未在 Windows 驗證」等舊敘述；它們不是本次執行結果。本報告以真實遠端、提交及事件證據說明本次 Windows／GitHub 示範。候選階段未改動這些來源文件，以免變更已鎖定版本。
- 本文件仍為候選報告；尚未產生此次正式 `final_report.md`、`final.json` 或 `final_result`，也尚未執行實際儲存庫的 `final-confirm`。

## Contributors

實際操作者：本作業使用者，共一人，負責三份獨立 clone 與三個本機 AI 對話的操作、任務指示及最後人類審閱。以下 P17／P22／P31 為本次單人示範的角色身分，不能將成員登記或 Git 身分計算為三位真人。

| 模擬身分 | 實質貢獻 |
| --- | --- |
| P17（成員檔顯示名稱：張子晴） | 初期測試證據發布、事件型別驗證、協定相容性及錯誤輸入測試。成員檔名稱不構成另一位真人參與的證據。 |
| P22（模擬組員B） | STATUS 精確提交測試證據、回歸測試、繁體中文文件；P17 審查與正常整合；300 秒修正、docstring 協作分工、P31 衝突解決、canonical 接受及此次候選報告。 |
| P31（模擬組員C） | docstring 的 GitHub 用途及執行需求說明、獨立發布及同一行衝突示範。 |

本機 AI 協助各角色實作、審查、測試及執行 Git/groupctl。AI 不列為額外真人組員，也不代替人類確認。

## Pending Work and Review Dispositions

本次 FINAL 準備前探索到 10 筆事件：4 筆 change_published、3 筆 test_result、1 筆 accept review、2 筆成功 integration_result。四項發布提交均納入 main；沒有未納入的已發布功能提交，也沒有 question、answer、blocker 或負面 review 事件。

P17 的正向 review 已由正常整合及後續完整測試承接。P22／P31 發布紀錄中「尚待整合的 docstring 衝突」是當時狀態，已由 `E-20261016T085350Z-P22-5618d4573116` 解決。120 秒逾時已調整並取得後續通過證據，未用理由文字豁免仍然失敗的檢查。仍存在的範圍與證據限制已列於 Known Limitations。

本次外部 decisions JSON 為 `{}`，因為沒有待處置的未納入改動或阻擋事件；不是用空處置跳過檢查。FINAL 新增測試與候選事件均已發布。剩餘步驟為實際操作者閱讀本報告並明確確認；在此之前不執行 final-confirm。
