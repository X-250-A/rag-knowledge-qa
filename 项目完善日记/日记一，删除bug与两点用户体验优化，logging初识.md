## 今日完成：

- ##### 评估器代码的完成与知识库的搭建

  - 评估器的逻辑均由AI完成，我后面需要读源码总结逻辑。这里就不展开了

- ##### 用户体验优化——查重逻辑，查阅权限校验的添加

  - 查阅权限的问题，其实很好解决，直接从current_user取id字段进行校验即可

  - 查重逻辑这块，只需要在create_document前进行文件名校验就好了，出现重名抛400异常即可。

- ##### bug修复，删除failed to fecth错误

  - 删除成功但报failed to fetch错误，但后续继续删除报Not Found。这是后端返回已删除的ORM模型的根因。

    - 这里是写CRUD时的失误，误返回了已删除ORM对象。

    - 这里还顺便增强了删除代码的健硕性。采用try--except包裹相关删除代码，包括删除向量库，删除磁盘文件。同时在dsh提示下，我得知了：unlink()本身执行删除操作，但windows中可能无法删除，例如文件进程被占用。所以，这里采用unlink() + exists()进行复查。

- ##### logging的涉猎与添加

  - 先前我甚至没有打印或保留报错信息的意识。今天被dsh启发，决定添加logging库助力找bug。

    - 单独创建logging_config文件写logging逻辑，与FastAPI解耦，方便复用

    - 写setup_logging函数，内部完成basicConfig配置

      - 一般写level和format参数，windows系统指定encoding=utf-8

      - 注意，如果要加上encoding参数，必须添加filename才不报错

    - 设置logging.getLogger().setLevel()压缩无用消息，例如sql语句

    - 利用Pathlib库，使文件摆脱硬编码，增强文件的可迁移性。

      - 这里Path(__ __file__ ____).resolve()的resolve是一层保险，保证文件路径为绝对路径。

      - 使用mkdir增强程序自愈能力（从github克隆的项目一般不包含logs，保留mkdir可以在缺乏相关文件夹时直接创建），即使Logs存在也不报错。

    - 在main.py导入并直接写出setup_logging函数即可注册完成





## 笔者有感：

        感觉今天干的事很多了，至少我的工程化素养似乎显著提升了。评估器逻辑明天再看吧，下机！
