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

以上只是示例，須改成目標專案真的存在的檔案與測試。每個命令是 argv 陣列，不使用 shell。`{python}` 代表執行 groupctl 的 Python。檢查會在指定 commit 的臨時 worktree 執行，時限每命令 120 秒。測試需要的外部環境仍須自行安裝。checks 是本實作的可選擴充欄位，原規格必要欄位保持原義。

## 驗證範圍與限制

已在 Linux + Python + Git 實測；未在 Windows 執行驗證。程式使用跨平台標準函式庫，Windows 指令已提供。
本次沒有連接使用者 GitHub，沒有替使用者真正提交小組成果。正式驗收仍須在你們共用的 GitHub repository 重跑真人＋AI 流程。
工具不自行產生 AI 語意判斷、不串接任何 AI API、不做 Dispatcher 或跨組任務分配。私有本機狀態不進 Git。敏感檔案偵測是輔助，AI/人仍須審查。
測試統計數字是「執行的檢查命令」數量，不是假裝取得測試框架內部案例數。
事件修改偵測依賴已取得的 Git 歷史；系統假設可信組員，不提供安全身分授權或防惡意改寫歷史機制。
