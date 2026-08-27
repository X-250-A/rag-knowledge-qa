## 今日成就：

- ##### 在hermes辅助下完成分块 -> 向量化 -> 入库 -> 查询的RAG基本流程闭环
  
  - 手写分块器逻辑函数，以及入库与查询逻辑函数。这块今天花的时间比较久，不过好处是了解了RAG的原理，以后直接AI生成，排错也从原理入手让AI排错。挺好。
  
  - 独立编排了上述函数，写在pipelines文件中

- ##### 重温PromptBuilder类和LlmClient类的初始化和部分函数构建流程
  
  - 我觉得正好总结一下这两个agent必备类的构建一般流程
  
  - PromptBuilder类：
    
    - 写在services目录下，代表编排逻辑
    
    - 使用Pathlib在self函数下初始化身份的system_prompt
      
      - ```
        path = Path(__file__).parent/"绝对路径1或parent"/"文件名.后缀"
        self.system_prompt = path.read_text("utf-8")
        ```
    
    - 初始化某空字符串变量，后续f-string拼接字符串
    
    - 返回纯字符串
      
      - 对于初始的system_prompt，采用list[dict]的结构更好，这样可以采用解包语法，后续需要添加偏好，会话上下文等内容时不需要重新return新的f-string字符串
  
  - LlmClient类：
    
    - 同样写在services下
    
    - 实例化httpx_client这个异步网络层客户端（AsyncClient）类对象
    
    - 实例化AsyncOpenAI异步OpenAI客户端类对象，把httpx_client作为参数传入
    
    - 写非流式聊天异步函数chat
      
      - ```
                kwargs = {
                    "model" : self.model,
                    "timeout" : settings.LLM_REQUEST_TIMEOUT,
                    "messages" : messages,
                }
                response = await self.client.chat.completions.create(**kwargs, stream=False)
                return response.choices[0].message.content
        ```
      
      - 这里用list[dict]的目的也是方便解包，与上面的目的一致



## 笔者有感：

        其实我感觉今天完成的内容没有昨天多，但了解到的RAG的按字数切块的基本原理，还是挺高兴的，同时重温了PromptBuilder和LlmClient的构建基础逻辑，下次应该就不需要回看项目代码了。总之还是在进步的。加油吧

        
