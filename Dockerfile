FROM public.ecr.aws/lambda/python:3.12

# 依存関係をコピー
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# 関数コードをコピー
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# ハンドラーを設定
CMD [ "lambda_function.lambda_handler" ] 