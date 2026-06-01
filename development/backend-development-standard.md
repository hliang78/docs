# OneOPS 后端开发规范

本文档沉淀 `docs/prompts` 中关于 Spring Boot/Nebula/Service/Repository/Controller 的经验，同时适配当前 OneOPS 多子项目现状。

历史 prompts 中有大量 Java/Spring Boot 2.6.9/Nebula 约束。它们对 Java 模块仍有参考价值，但当前仓库还包含 Go、前端、Agent、Telegraf 等子项目，因此本规范分为“通用原则”和“Java/Nebula 参考规范”。

## 通用原则

- 优先遵循目标子项目现有框架、目录结构和代码风格。
- 修改前先识别模块边界、数据来源、调用链和测试入口。
- 不跨边界修改无关模块。
- 对外部系统、真实设备、凭证、任务下发、数据写入保持显式安全边界。
- Read-only discovery、dry-run、controlled action、external/device action 必须分开。
- 所有业务成功判断必须看业务响应字段或状态，不只看 HTTP 200。
- 所有新增行为必须有测试或 evidence。

## 模块边界

实现前必须确认：

| 问题 | 说明 |
|---|---|
| 目标子项目 | `OneOPS`、`OneOPS-UI`、`agent`、`teleabs`、`telegraf` 等 |
| 目标模块 | 设备、监控、日志、拓扑、凭证、任务中心等 |
| 写入范围 | 本次允许修改哪些目录/文件 |
| 数据边界 | 是否读写 DB、缓存、文件、外部系统 |
| 设备边界 | 是否触碰真实设备或网络命令 |
| 安全边界 | 是否接触 credential、token、SNMP community、private key |
| 审批边界 | 是否需要 human approval |

## 分层要求

无论具体语言和框架如何，后端模块建议保持以下逻辑分层：

```text
HTTP/RPC handler
  -> application/service
  -> domain logic
  -> repository/data access
  -> external client / DB / cache / queue
```

要求：

- handler/controller 只做协议适配、参数绑定、权限入口、响应包装。
- service/application 层承载业务编排、状态流转、边界校验。
- repository/data access 封装 DB/Mapper/ORM，不把 SQL/存储细节泄漏到 service。
- external client 封装外部 API、设备、Prometheus、Loki、Agent、任务系统调用。
- 业务对象、持久化对象、API DTO 不应随意混用。

## 参数校验

所有 public service/handler 入口都必须做边界校验：

- 必填字段不能为空。
- 字符串长度符合业务或 schema 限制。
- 数值范围合法。
- 集合不应为 null；空集合是否允许要明确。
- tenant/device/fixture 范围必须可证明。
- credential 只能传 reference，不能传 secret value。
- 写操作必须确认权限和幂等性。

Java 模块可使用 `org.apache.commons.lang3.Validate`，Go 模块应使用项目既有 validation/error pattern。

## 错误处理

- 不要吞掉异常。
- 不要只打印日志后继续返回成功。
- 错误信息要能定位输入、状态、外部依赖或权限问题。
- 不向用户或 evidence 输出 secret。
- 事务中 catch 异常时必须确认是否会导致 rollback 失效。
- 外部调用失败应记录 dependency、operation、target alias、request id/run id。

## 数据访问

要求：

- Service 不直接拼 SQL。
- 查询结果为空时返回空集合，而不是 null，除非接口约定明确允许 null。
- 写操作必须说明唯一约束、幂等策略、软删除策略。
- 大批量操作要考虑分页、批大小、超时、重试。
- 对 tenant/device/source 的查询必须有范围约束，避免跨租户或误打非 fixture。

数据库设计文档应同步说明：

- 表结构。
- 索引。
- 状态字段。
- 审计字段。
- 软删除字段。
- 数据量预估。
- 迁移策略。

## API/Controller 要求

- 一个业务 service 通常对应一组清晰的 API handler/controller。
- API path 应表达资源与动作，避免纯方法名泄漏。
- 查询类接口使用 GET 或项目既有查询方式。
- 写入类接口使用 POST/PUT/PATCH/DELETE 或项目既有写入方式。
- 响应统一包装，保持项目现有响应结构。
- Controller/handler 必须捕获可预期业务异常并返回标准错误结构。
- Swagger/OpenAPI 或接口文档必须同步更新。

历史 Java/Nebula prompt 中的参考约束：

- Controller 继承 `BaseController`。
- 返回 `ResponseModel`。
- 查询方法通常用 `GetMapping`。
- create/save/update 等写操作用 `PostMapping`。
- 根路径形如 `/v1/<module>/<feature>`。

这些约束只在对应 Java/Nebula 模块存在时适用。

## Java/Nebula 参考模块结构

历史 prompts 给出的标准业务模块是三段式：

```text
<rootpackage>/
  <rootpackage>.sdk/
  <rootpackage>.local/
  <rootpackage>.local.starter/
  pom.xml
```

职责：

- `sdk`: 对外暴露业务能力抽象、PO、event、strategy、service interface。
- `local`: 本地实现，包含 entity、repository、service impl、mapper。
- `local.starter`: Spring Boot 自动装配配置。

`local.starter` 应提供：

- `Config.java`
- `META-INF/spring.factories`
- `@EnableJpaRepositories`
- `@EntityScan`
- `@ComponentScan`

## Java Service/Repository 参考规则

Java/Nebula 模块可采用以下规则：

- Service interface 位于 `service/`。
- Service impl 位于 `service/internal/`。
- Repository 位于 `repository/`。
- Mapper 位于 `mapper/`。
- Po 位于 `po/`。
- Entity 不在普通 service story 中随意修改。
- Service 不直接注入 Mapper，统一通过 Repository。
- Entity 与 Po 转换使用 `NebulaToolkitService`，避免手工逐字段复制。
- public Service 方法必须有 JavaDoc。
- JDK 8 兼容。
- Google Java Style，2 spaces 缩进。

方法命名参考：

| 类型 | 命名 |
|---|---|
| 单条件查询 | `findBy<FieldName>` |
| 多条件查询 | `findBy<Field1>And<Field2>` |
| 统计查询 | `countBy<Condition>` |
| 聚合查询 | `sumBy<Field>` |
| 复杂条件查询 | `findByConditions` |
| 通用查询 | `findAll`、`findById` |

## 事务与并发

事务检查：

- `@Transactional` 应用于有效 public 方法。
- catch 块不能吞掉需要回滚的异常。
- 查询方法可设置 `readOnly = true`。
- 谨慎使用 `REQUIRES_NEW`。
- 外部系统调用不要随意放入长事务。

并发检查：

- 避免直接 `new Thread()`。
- 避免不受控的 cached thread pool。
- 任务调度、agent worker、loop 要有状态、锁、重试、超时和日志。
- 缓存策略必须说明一致性要求。

## 缓存

- Redis 适合跨实例共享、需要集中失效的数据。
- 本地缓存适合读多写少、数据量可控、一致性要求不高的数据。
- 使用本地缓存必须说明多实例不一致风险。
- 不要在 Redis 中存储过大 JSON 对象而没有 TTL、版本和失效策略。

## 安全与 secret

禁止：

- 在代码、日志、evidence、测试报告中写入 password、token、private key、SNMP community、bearer token。
- 把 credential value 当作普通字段传递或持久化。
- 在自动化任务中执行未经 approval 的真实设备命令。

允许：

- credential ref。
- redacted id。
- presence boolean。
- endpoint alias。
- test-only fixture identity。

## 完成定义

后端 story 完成时应具备：

- 代码实现完成。
- 接口/数据/设计文档已同步。
- 测试通过或说明未能执行的原因。
- evidence 包含命令、环境、输入、输出、结论。
- 如有 H0/H1 风险，已修复或明确阻塞/审批。

