FROM public.ecr.aws/lambda/python:3.12

# 依存関係をコピー
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# 全ファイルをコピー（ローカルテストやCLIも動かせるように）
COPY . ${LAMBDA_TASK_ROOT}
WORKDIR ${LAMBDA_TASK_ROOT}

# デフォルトはLambdaハンドラー
CMD [ "lambda_function.lambda_handler" ] 