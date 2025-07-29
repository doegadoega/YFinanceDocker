@echo off
REM === YFinance API デプロイ（Windows版） ===
echo === YFinance API デプロイ開始 ===

REM AWS 認証情報を確認
echo AWS 認証情報を確認しています...
aws sts get-caller-identity
if %ERRORLEVEL% neq 0 (
    echo エラー: AWS認証情報が設定されていません
    exit /b 1
)

REM 設定
set BUCKET_NAME=yfinance-api-deploy-%RANDOM%
set STACK_NAME=yfinance-api-stack
set REGION=ap-northeast-1

echo デプロイユーザー: 
aws sts get-caller-identity --query "Arn" --output text
echo S3バケット: %BUCKET_NAME%
echo CloudFormationスタック: %STACK_NAME%
echo リージョン: %REGION%

REM S3バケットを作成
echo S3バケットを作成しています...
aws s3 mb s3://%BUCKET_NAME% --region %REGION%

REM 既存のスタックを確認
echo 既存のスタックを確認しています...
aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %REGION% >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo 既存のスタックが見つかりました。更新モードでデプロイします...
) else (
    echo 新規スタックを作成します...
)

REM SAM ビルド
echo SAM ビルドを実行しています...
sam build
if %ERRORLEVEL% neq 0 (
    echo エラー: SAM ビルドに失敗しました
    exit /b 1
)

REM SAM デプロイ
echo SAM デプロイを実行しています...
sam deploy --stack-name %STACK_NAME% --s3-bucket %BUCKET_NAME% --capabilities CAPABILITY_IAM --region %REGION%
if %ERRORLEVEL% neq 0 (
    echo エラー: SAM デプロイに失敗しました
    exit /b 1
)

echo === デプロイ完了 ===
echo API Gateway URL:
aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %REGION% --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" --output text

pause 