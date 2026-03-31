import multiprocessing

# Gunicorn 生产环境推荐配置
# 运行命令: gunicorn -c gunicorn.conf.py app:app

# 绑定的网络地址
bind = "0.0.0.0:5000"

# 工作模式
# 遇到依赖网络 I/O 较多（例如请求 Google Gemini / 发送邮件）的服务，
# 建议切换为异步方式，如 'gevent' 或 'eventlet'，需额外 pip install gevent
worker_class = "gthread"
threads = 4

# worker 数量：推荐为 CPU 核心数 * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1

# 最大请求超时时间（简历分析可能耗时超过30秒）
timeout = 120

# 限制客户端请求头和报文大小防攻击（可选）
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 记录错误和访问日志
errorlog = "data/error.log"
accesslog = "data/access.log"

# 日志格式
loglevel = "info"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
