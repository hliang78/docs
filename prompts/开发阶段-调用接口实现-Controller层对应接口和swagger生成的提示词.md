
请在controller层，基于{root.service}指定的服务层接口，生成controller层的http restful接口逻辑。

# 基本生成要求
以下是一个生成范例：
...java
@Slf4j
@RestController
@RequestMapping("/v1/decision/process")
public class DecisionProcessController extends BaseController {
  @Autowired
  private DecisionProcessService decisionProcessService;
  
  /**
   * 查询所有可用的决策分析处理器（决策模型）
   * @return 决策分析处理器列表
   */
  @GetMapping("/findAll")
  public ResponseModel findAll() {
    try {
      List<Pair<String, String>> results = this.decisionProcessService.findAll();
      return this.buildHttpResult(results);
    } catch(RuntimeException e) {
      log.error(e.getMessage(), e);
      return this.buildHttpResultForException(e);
    }
  }
}
...

以上范例中要注意几个类型

a、所有controller层实现都要和指定的service接口有一对一的关系，例如有一个DecisionProcessService就会有一个DecisionProcessController
b、所有controller层的实现类，都必须继承com.bizunited.nebula.common.controller.BaseController，其中有一些关联的controller工具
c、具体的controller方法只有GetMapping和PostMapping两种请求方式，命名为find、count、group这样的查询性质的方法，使用GetMapping；命名为save、create、udpate这样的写操作方法，使用PostMapping；
d、所有controller方法的返回对象，只能是com.bizunited.nebula.common.controller.model.ResponseModel对象，而ResponseModel对象可以由BaseController中的共用工具进行生成，具体来说有这样一些工具方法：
...java
  /**
   * 当异常状况时，使用该方法构造返回值
   * @param e 错误的异常对象描述
   * @return 组装好的异常结果
   */
  protected ResponseModel buildHttpResultForException(Throwable e);
  
  /**
   * 该方法不返回任何信息，只是告诉调用者，调用业务成功了。
   * @return
   */
  protected ResponseModel buildHttpResult();
  
  /**
   * 该方法不返回任何信息，只是告诉调用者，调用业务成功了。
   * @return
   */
  protected ResponseModel buildHttpResult(Object data);
  
  /**
   * 基于白名单关联属性过滤的查询结果对象构建方法<br>
   * 例如返回user下面的基本信息，包括user下的所有roles关联信息，那么白名单中需要包括roles属性即可，其它的关联属性都将被剔除。
   * @see #buildHttpResultW(entity, String...)
   * @param properties
   * @return
   */
  @SuppressWarnings("unchecked")
  protected <T> ResponseModel buildHttpResultW(Page<T> page, String... properties);
...

e、controller中，根级url的命令方式为
/v1/模块名/功能名
例如以上的示例代码中，/v1/decision/process，decision表示是模块名（决策模块）；process表示是功能名（流程功能）

# 关于swagger相关注释的说明
虽然以上内容中，并没有swagger的相关注释，但是你应该在controller层的类中，做相关swagger注释的生成

# 生成规范
1、请使用JDK 8的支持
2、代码风格为 google for java style，最典型的要求，就是保证为两个空格做为缩进，而不是Tab做为缩进
3、请保证java文件名命名的规范性
4、数据层/持久层模型需要支持JPA-hibernate也需要同时支持mybaits，也就是说需要同时使用两种数据层框架的标准注释

# 关键变量信息
{root.service}: # 请指定/拖拽根文件夹

如果使用者没有指定{root.service} 这个变量，你可以拒绝生成