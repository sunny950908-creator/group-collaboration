# 實際 GitHub 驗收步驟

這份流程尚未在你的 GitHub 執行。先完成本機 demo，再逐項操作。請使用專用作業 repository，避免影響其他專案。

1. 確認每位成員都有 Python 3.10+、Git、可操作本機檔案與終端機的 AI，以及自己的 GitHub 存取權。不要把密碼或 token 寫入作業。
2. 在 GitHub 建立共用儲存庫，讓三位組員可存取。複製本專案檔案進儲存庫，使用 main 作為 canonical branch。
3. 第一位成員在 repository 根目錄執行：

   `py groupctl.py init --group G-12 --person P17 --name "組員A" --assignment specs/00_group_collaboration_assignment.md`

   檢查並設定 `.group/group.json` 的 checks，測試命令可使用 `{python} -m unittest discover -s tests -v` 的 argv 陣列形式。以 Git 明確 add、commit、push 初始化內容。Git user.name / user.email 應使用自己要公開在 commit 的資料。
4. 另外兩人各自 clone 同一 repository，各自執行 `join --person P22 --name "組員B"`、`join --person P31 --name "組員C"`，登記檔依序提交整合到 main，避免起步時的同步競爭。第一位同步登記結果。
5. 各自建立個人分支，例如 `git switch -c people/P17/parser`。不要共用個人分支。每個 clone 以 join 設定自己的本機身分。
6. 把 AGENT_INSTRUCTIONS.md 和 specs/ 交給每位 AI，說明這些是本作業協作程序。人類協調兩個獨立變更，由各自 AI 實作。不要讓 AI 只回覆「完成」而不操作真實工具。
7. A 對 AI 說 PUB；記下回傳的真實 C-... 編號。B 說 SYNC，確認能從 A 的遠端分支讀到事件。B 說 REV C-...，審查後再說 INT C-...。保留整合與測試事件。
8. 設計一個不同檔案的正常合併案例，以及同一行不同修改的衝突案例。衝突時讓 AI 說明雙方意圖並修正，不能直接忽略一邊。修復後重新驗證與發布 integration_result。
9. 再示範「文字可合併但介面不相容」案例，例如 producer 回傳字典、consumer 仍呼叫字串方法。Git 無衝突不等於成功；測試與語意審查必須抓到問題。
10. 執行 TEST，確認其他成員 SYNC 可看到 test_result，且紀錄確切 commit。處理所有重要問題後，明確把接受的分支合入 main，檢查、測試並 push。
11. 任一成員對 AI 說 FINAL。AI 整理未採用改動、審查與測試證據，產生 candidate.md。學生實際閱讀並確認之後，才可執行 final-confirm --human-confirmed。若還有重要未完成工作，應先處理。
12. 驗收提供 repository、操作過程、事件與測試證據，以及 `.group/final/final_report.md`、`final.json` 指向的 canonical commit。正式結果來自 main，不是某人的私人分支。

教授沒有在這八份規格指定繳交網站、影片格式或截止時間；這些請依課堂公告，不能自行猜測。
