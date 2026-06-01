# Test Service

这是一个基于Spring Boot 2.6.9的测试服务项目。

## 项目结构

```
service/
├── pom.xml                                    # Maven配置文件
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── biz/
│   │   │           └── test/
│   │   │               ├── TestServiceApplication.java    # 主启动类
│   │   │               ├── config/                        # 配置类
│   │   │               ├── controller/                    # 控制器层
│   │   │               ├── entity/                        # 实体类
│   │   │               ├── mapper/                        # MyBatis Mapper
│   │   │               ├── repository/                    # JPA Repository
│   │   │               ├── service/                       # 服务层接口定义
│   │   │               │     └──internal/                 # 服务层逻辑的具体实现
│   │   │               └── utils/                         # 工具类
│   │   └── resources/
│   │       └── application.yml                            # 主配置文件
│   └── test/
│       └── java/                                          # 测试代码
```

## 技术栈

### 基本技术栈
- **Spring Boot**: 2.6.9
- **Spring Data JPA**: 数据访问层
- **MyBatis Plus**: ORM框架
- **MySQL**: 数据库
- **Redis**: 缓存和会话存储
- **Druid**: 数据库连接池
- **Lombok**: 代码简化
- **Maven**: 项目管理

### 自定义maven仓库所需要引入的依赖

自定义maven仓库的地址为：http://maven.biz-united.com.cn:28080/artifactory/libs-release-local
 - com.biz-united.nebula.utils:nebula-utils  nebula 基础工具包  版本 2.4.3.0
 - com.biz-united.nebula.security:security-local-starter  nebula  基础权限工具包  版本 2.4.3.0

## 配置说明

### 数据库配置
- 主机: localhost
- 端口: 3306
- 用户名: root
- 密码: 123456
- 数据库: test_db

### Redis配置
- 主机: localhost
- 端口: 6379
- 数据库: 0
- 无密码

## 启动方式

1. 确保MySQL和Redis服务已启动
2. 创建数据库 `test_db`
3. 运行主类 `TestServiceApplication`

```bash
mvn spring-boot:run
```

## 监控

- **Druid监控**: http://localhost:8080/test-service/druid/
- **Actuator健康检查**: http://localhost:8080/test-service/actuator/health

## 注意事项

1. 项目使用UTF-8编码
2. Java代码遵循Google Java Style规范
3. 使用2个空格缩进
4. 异常处理优先使用IllegalArgumentException
5. 集成了nebula安全框架
