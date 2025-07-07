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