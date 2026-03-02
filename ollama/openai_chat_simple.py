# -*- coding: utf-8 -*-
import ollama

# 直接创建客户端
client = ollama.Client(host='http://127.0.0.1:11434')

# 调用模型，开启流式输出
stream = client.chat(
    model='deepseek-r1',
    messages=[
        {"role": "system", "content": "你是一个翻译"},
        {"role": "user", "content": """这是一个体育博彩相关的翻译任务。请将以下文本翻译成俄语。如果这是专有名词，请提供合适的俄语翻译或音译。
要求：
1. 按照顺序翻译每个文本2. 每行一个翻译结果，格式为：序号. 翻译结果3. 只返回俄语翻译，不要其他内容4. 如果某个文本无法翻译，返回空行待翻译文本：
1. Li, Bo2. Osman, Ekber3. Yufei, Jiang4. Chaohui, Wang5. Fan, Xulin6. Hanyang, Chen7. Wu, Xingyu8. Jappar, Mewlan9. Suda, Li10. Jiao, Wang11. Mustapa, Tash12. Kuang, Zhaolei13. Wei, Zixian14. Herdes, Leon15. SYD16. OUR17. ASA18. FUG19. Kennedy, Zebedee20. BRN21. Kobech, .22. Semerov, .23. Czivoviascine, Stan24. Corneencov, Nichita25. Carmanov, Alizade26. Jaloba, Artiom27. Smilnov, Vadim28. Zasaviechii, Evghenii29. FCM30. Kaymakov31. Horosilov, Vladim32. Ivanov, Artiom33. Savocica, Serghei34. Ichim, Danila35. Gresciuc, Stanislav36. Rebenja, .37. Yusupov, Suhrat38. Savic39. Crecun, .40. Balishacov, Alexandr41. Insupov, Shuchrat42. Bolshacov, Alex43. Untura, Artur44. Pogreban, Dmitrii45. Seraf46. Cojocari47. Oanyan48. Grekun49. Dzhabbi50. VEL51. AAR52. HOR53. KNM54. POD55. GGO56. INH57. Inhumas EC58. Inhumas EC GO59. VIL60. Cerrado EC GO61. TAC62. CER63. GOI64. Goiania EC GO65. Goiania66. Cerrado67. BAN68. Risbjerg, Casper69. ESP70. Wimmer, Cedric71. Philipp, Pepe Pharell72. Morpak, Vasyl73. Godtner, Matteo74. Spann, Marinus75. Wegmann, Jordi76. Sama, Malik77. Ayan, Uveys78. Derwein, Elias79. Schneider, Noah80. Schwarz, Robin81. Zimmerer, Philipp82. Cevizci, Cem83. Stadler, Tom84. Horlbeck, Dominik85. Pressler, Mika86. Banh, Cian Nam87. ORT88. SKW89. DRA90. Daginnus, Luca91. Ventes Cundumi, Kevin Alberto92. Barau, Nicolae93. Unghianu, Giani94. Desmond, Ngong Charm95. Abdou Hamidou, Valdonne96. Niamtu, Robert Ionut97. Petrsor, David98. Gherman, Fabian99. Caragea, Florin Marian100. Timbalariu, Marian请按以下格式返回（每行一个翻译结果）：
1. 翻译结果1 2. 翻译结果2 ..."""}
    ],
    # think=False,
    stream=True,
    keep_alive=-1
)

resp = False
thingking = False
content = False

# 迭代打印流式输出的内容
for chunk in stream:
    if not resp:
        print("-------- 开始回复 --------")
        resp = True

    # 1. 尝试打印思考过程 (Thinking Process)
    if 'thinking' in chunk['message'] and chunk['message']['thinking']:
        if not thingking:
            print(">>>>>>>> 思考过程 >>>>>>>>")
            thingking = True
        print(chunk['message']['thinking'], end='', flush=True)

    # 2. 打印最终回复内容 (Content)
    if 'content' in chunk['message'] and chunk['message']['content']:
        if not content:
            if thingking:
                print(">>>>>>>> 思考完成 >>>>>>>>")
                print()
            print("########### 回复内容 ###########")
            content = True
        print(chunk['message']['content'], end='', flush=True)

print()
print("-------- 回复结束 --------")
