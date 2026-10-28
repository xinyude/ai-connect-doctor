# AI Connect Doctor

A small local diagnostic tool for common AI development environment issues. It uses the Python standard library and does not call an AI API.

## Quick start

Requires Python 3.9 or newer. From this directory:

```sh
python -m ai_connect_doctor
python -m ai_connect_doctor --json
python -m ai_connect_doctor --dns example.com
python -m ai_connect_doctor --url https://example.com
```

The default report checks Python, OS, TLS library and whether proxy variables are set. It flags bracketed IPv6 in `NO_PROXY` as a potential compatibility issue, not a confirmed error. DNS lookup is optional and discloses the requested host to the configured DNS resolver. The optional HTTPS check sends a HEAD request to the specified origin, using system proxy settings; it sends no API key and follows no redirects. A server response does not prove that an AI API or credentials work. The tool does not change system settings.

Proxy variable values, hostnames, passwords and API keys are not included in reports. Review reports before sharing; environment information itself can still be identifying. No telemetry is collected.

## Run tests

```sh
python -m unittest discover -s tests -v
```

## 中文说明

这是一个本地 AI 开发环境诊断工具，默认不联网、不调用模型 API，也不修改系统配置。它显示 Python 和 TLS 版本、检查代理变量是否设置，并提示 `NO_PROXY` 中可能影响部分 HTTP 客户端的 IPv6 写法。指定 `--dns 域名` 可选择进行 DNS 查询；指定 `--url https://域名` 可发送 HEAD 请求检查 HTTPS 连接。该请求使用系统代理，不携带密钥、不跟随跳转；服务器响应不代表 API 或凭据可用。报告不显示代理地址、密码或密钥；分享前仍请自行检查。
