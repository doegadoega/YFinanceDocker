# YFinance API - Windows環境セットアップガイド

## 🪟 Windows環境での完全セットアップ

### 1️⃣ **必要なソフトウェアのインストール**

#### **Docker Desktop**
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) からダウンロード
2. インストール後、Docker Desktopを起動
3. 確認: `docker --version`

#### **AWS CLI**
1. [AWS CLI v2](https://aws.amazon.com/cli/) からダウンロード
2. `aws-cli-setup.exe` を実行してインストール
3. 確認: `aws --version`

#### **AWS SAM CLI**
1. [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) からダウンロード
2. `sam-installation.msi` を実行してインストール
3. 確認: `sam --version`

### 2️⃣ **AWS認証設定**

#### **PowerShell / Command Prompt で実行**
```cmd
aws configure
```
入力項目:
- AWS Access Key ID: `あなたのアクセスキー`
- AWS Secret Access Key: `あなたのシークレットキー`
- Default region name: `ap-northeast-1`
- Default output format: `json`

### 3️⃣ **デプロイ実行**

#### **方法1: バッチファイル（推奨）**
```cmd
deploy.bat
```

#### **方法2: 個別コマンド**
```cmd
REM SAM ビルド
sam build

REM SAM デプロイ
sam deploy --guided
```

### 4️⃣ **ローカルテスト**

#### **Docker環境でのテスト**
```cmd
REM Dockerイメージをビルド
docker-compose build yfinance-local

REM ローカルサーバー起動
docker-compose up yfinance-local

REM 別のターミナルでテスト
curl "http://localhost:8000/ticker/basic?ticker=AAPL"
```

### 5️⃣ **PowerShell用テストコマンド**

```powershell
# PowerShellでのAPI テスト
Invoke-RestMethod -Uri "http://localhost:8000/ticker/basic?ticker=AAPL" -Method GET

# または
Invoke-WebRequest -Uri "http://localhost:8000/search?query=Apple" -Method GET
```

## 🚨 **トラブルシューティング**

### **Docker関連エラー**
```
Error: Docker daemon is not running
```
**解決**: Docker Desktopを起動してください

### **AWS認証エラー**
```
Error: Unable to locate credentials
```
**解決**: `aws configure` で認証情報を設定してください

### **SAM関連エラー**
```
Error: SAM CLI not found
```
**解決**: SAM CLIを再インストールしてください

## 📦 **インストール確認コマンド**

```cmd
REM すべてのツールが正しくインストールされているか確認
docker --version
aws --version
sam --version
git --version
```

## 🎯 **Windows特有の注意点**

1. **パス区切り文字**: `\` を使用（自動変換される）
2. **権限**: 管理者権限不要（Docker Desktop設定による）
3. **ファイアウォール**: Docker Desktop初回起動時に許可が必要
4. **WSL2**: Docker Desktopが自動でセットアップ

## 💡 **エディター推奨設定**

### **Visual Studio Code**
```json
{
  "terminal.integrated.defaultProfile.windows": "Command Prompt",
  "files.eol": "\n"
}
```

これで、Windows環境でも完全にプロジェクトが動作します！
