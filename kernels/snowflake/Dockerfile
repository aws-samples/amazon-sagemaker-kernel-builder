FROM public.ecr.aws/lambda/python:3.7

RUN pip install sagemaker==2.36.0 && \
    pip install --upgrade snowflake-connector-python[pandas]==2.4.2 && \
    pip install matplotlib==3.4.1 && \
    pip install ipywidgets seaborn scikit-plot fsspec s3fs && \
    pip install ipykernel && \
    python -m ipykernel install --sys-prefix && \
    pip install jupyter_kernel_gateway