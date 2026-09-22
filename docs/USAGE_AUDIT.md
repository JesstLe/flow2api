# 用量审计

## 统计口径

管理员页面的“用量审计”读取 request_logs，按请求发生时间聚合，默认展示最近 7 天，可切换为 1、30、90 或 365 天。统计接口为 GET /api/usage/audit，仅接受管理员会话。

- 成功：HTTP 状态码 200-299
- 失败：HTTP 状态码 >=400
- 处理中：HTTP 状态码 102
- 图片：generate_image
- 视频：generate_video 或 extend_video
- 未分配：请求日志没有关联 Flow Token

页面提供总量、成功/失败、图片/视频、平均耗时、活跃账号，以及按 Token、日期、模型和最近请求的明细，并支持 Token、操作、状态筛选。

## 审计边界

当前账号维度是 Flow2API 的 Flow Token/账号（request_logs.token_id 关联 tokens），不是 New API 最终用户身份。统计响应只返回聚合字段和最近请求的元数据，不返回 request_body 或 response_body，避免在审计列表中泄露生成内容和调用参数。

如果后续需要审计 New API 的最终调用者，需要在请求日志中增加调用方标识（例如 X-User-ID 或 X-User-Email）并单独迁移字段。
