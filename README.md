# Maplestory
Python Script
python -m venv .venv
.\.venv\Scripts\Activate.ps1
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

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

步驟 1：安裝 Tesseract-OCR 主程式（不是 Python package！）
下載 Windows 安裝程式：官方 Windows 版本下載點（GitHub Releases）

下載例如「tesseract-ocr-setup-5.3.4.20240109.exe」或最新安裝包。

直接執行安裝，建議路徑：

makefile
複製
編輯
C:\Program Files\Tesseract-OCR\
安裝時勾選「Add to PATH」選項（這樣 python 就能直接找到執行檔）。

步驟 2（可選）：如果你沒加到 PATH
可以在程式開頭加一行指定路徑，例如：

python
複製
編輯
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
請確認 tesseract.exe 真的在這個路徑，否則請改成你安裝的實際路徑。

