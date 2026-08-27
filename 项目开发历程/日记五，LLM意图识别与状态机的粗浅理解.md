## 昨日完成：

- ##### LLM轻量意图识别函数的完成
  
  - 仿写上一个项目的意图识别函数，现在总结一般流程：
    
    - 构造message的list[dict]型数据，为后续调用OpenAI的SDK需要传入的message参数做准备
      
      - 注意，message需要包含的内容有system_prompt，context_hint，user_input，即意图识别器的系统提示词，会话历史上下文与用户输入，上下文的注入要经过if检查，用户输入为必注入项。
    
    - 调用SDK并接收LLM答案
      
      - 一般system_prompt中都会要求LLM输出标准JSON格式的字符串
    
    - json.dumps转化返回结果为JSON格式数据
    
    - 返回意图判断结果

- ##### 完成SSE流式聊天基础组件
  
  - 将agent主入口的返回值改为异步返回事件{"type" : "event", "str" : "str"}，方便前端接收数据并打造打字机。
  
  - 在chat路由函数完成异步事件吞吐，了解了事件吞吐的约定格式：" data: {json.dumps( event ) } \n\n"



## 今日完成：

- ##### 完成chunk的CRUD撰写

- ##### 完成部分状态机撰写
  
  - 包括CRUD函数（update_document_state），额，好像也没别的了





## 笔者有感：

        感觉这两天懈怠了，干的活挺少的。不行，后面得提速了，额，明天干完行不行，最晚后天。要把前端一起干了。正好，上一个项目有模板，让opencode抄就行。



### 2026.8.26


