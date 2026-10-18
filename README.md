# Group Collaboration — protocol 0.1

Python 3.10+ 與 Git；只使用 Python 標準函式庫。這是教授八份規格的可執行初版。

## 先測試

Windows PowerShell（在本專案資料夾）：

```powershell
py --version
git --version
py -m unittest discover -s tests -v
py demo.py --output demo-output
```

macOS/Linux 將 `py` 換成 `python3`。demo-output 必須尚不存在。

`demo.py` 建立三個獨立 clone、三個個人分支、本機 bare remote，示範獨立開發、PUB、SYNC、正常整合、衝突、解決後驗證、TEST、canonical 接受與 FINAL。保留事件 JSON、Git 歷史、正式報告供檢查。示範的語意判斷、衝突修復、人類確認是腳本模擬，不能說成已由真人與 AI 完成。

## 檔案

- groupctl.py：協作 CLI，`py groupctl.py --help` 查看子命令。
- AGENT_INSTRUCTIONS.md：每位本機 AI 都要讀的操作說明。
- specs/：教授提供的八份原始規格，未修改。
- tests/test_workflow.py：真實 Git 端對端與安全性測試。
- demo.py：可重現三人本機示範。
- evidence/：本次測試輸出及示範產物。
- docs/GITHUB_DEMO.md：實際 GitHub 示範流程。

SYNC/PUB/INT/REV/TEST/STATUS/FINAL 是對 AI 說的提示指令；終端機執行的是 groupctl.py 子命令，兩者不完全一對一。AI 要依照 AGENT_INSTRUCTIONS.md 補上檢查與判斷。

## 設定測試

初始化後，在 `.group/group.json` 加入可選的 checks 設定，例如：

```json
"checks": {
  "build": [["{python}", "-m", "py_compile", "app.py"]],
  "tests": [["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"]]
}
```

以上只是示例，須改成目標專案真的存在的檔案與測試。每個命令是 argv 陣列，不使用 shell。`{python}` 代表執行 groupctl 的 Python。檢查會在指定 commit 的臨時 worktree 執行，時限每命令 300 秒。測試需要的外部環境仍須自行安裝。checks 是本實作的可選擴充欄位，原規格必要欄位保持原義。

## 驗證範圍與限制

初版本機測試記錄包含 Linux；本次課程示範另已在 Windows、Python 3.14.3、Git 2.55.0.windows.3 執行編譯與完整測試，17 個測試通過。實際結果應依 `.group/events/` 中各次測試的精確 commit 與命令輸出判讀，不將其他版本的結果視為目前 HEAD 的證據；尚無完整跨平台環境矩陣。
已使用真正 GitHub 儲存庫 https://github.com/sunny950908-creator/group-collaboration 完成發布、遠端事件探索、審查、正常整合、刻意 docstring 衝突與解決、測試證據發布及 canonical main 接受。示範由一位實際操作者管理三份獨立 clone、三個本機 AI 對話，以 P17／P22／P31 模擬三個角色，不代表三位真人參與。具體 change_id、整合事件與版本對照見 `.group/final/candidate.md`；結案程序仍依人類審閱確認規則執行。
「無文字衝突但行為不相容」由 `test_semantic_incompatibility_despite_clean_merge` 在臨時本機 Git 儲存庫重現，未另外在 GitHub 功能分支示範。`demo.py` 的本機 bare remote 與腳本模擬結果，應與上述實際 GitHub 操作分開描述。
工具不自行產生 AI 語意判斷、不串接任何 AI API、不做 Dispatcher 或跨組任務分配。私有本機狀態不進 Git。敏感檔案偵測是輔助，AI/人仍須審查。
測試統計數字是「執行的檢查命令」數量，不是假裝取得測試框架內部案例數。
事件修改偵測依賴已取得的 Git 歷史；系統假設可信組員，不提供安全身分授權或防惡意改寫歷史機制。
