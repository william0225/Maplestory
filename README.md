# Maplestory
Python Script
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 忽略 Python venv 及常見暫存
.gitignore內容
venv/
.env/
__pycache__/
*.pyc
*.pyo
*.pyd
.idea/
.vscode/
.DS_Store

1. 確認 Git 的路徑已加入 PATH
打開 Git Bash，執行：

bash
複製
編輯
which git
會出現類似：

bash
複製
編輯
/c/Program Files/Git/cmd/git.exe
複製該路徑（通常是 C:\Program Files\Git\cmd）

加入 Windows 環境變數 PATH

Windows 搜尋「環境變數」，點「編輯系統環境變數」→「環境變數」

在「系統變數」或「使用者變數」找到 PATH，點「編輯」

新增剛剛複製的路徑

確定全部視窗

重啟 VS Code（一定要！）

再開一個 VS Code Terminal（PowerShell/CMD）輸入：

css
複製
編輯
git --version
應該就能正常顯示了！

#####
你第一次用 git commit，git 告訴你「Author identity unknown」，要你設定 user.name 和 user.email。

你還沒設定過 git 的「身分資訊」。

現在 commit 不會成功，直到你設定完畢。

處理方式與說明
你只要執行下面兩行指令，把你的名字和 email 換成你自己的即可：
bash
複製
編輯
git config --global user.name "你的名字"
git config --global user.email "你的 email"
例如：

bash
複製
編輯
git config --global user.name "William"
git config --global user.email "william@example.com"
這樣會設定成「全系統預設」身分（推薦），以後所有 git 專案都會套用這個名字/email。

如果你只想針對單一專案設定（例如：家用/公司要分開）
把 --global 拿掉，這樣只會寫進目前專案：

bash
複製
編輯
git config user.name "William"
git config user.email "william@example.com"
設定完成後，再 commit 就不會跳錯
bash
複製
編輯
git commit -m "find boss first version"