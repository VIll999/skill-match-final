花了很久想做好这个project：第一步先建数据库填充数据，原计划写爬虫直接爬 Indeed，可是很快意识到自己写爬虫是短期内比较难以实现的，**因为现在大多数网站都有反爬虫保护机制**想首先快速填充数据**，选了 ``Adzuna`` 官方 API ``https://developer.adzuna.com/``，接口文档完整、字段标准化，缺点是数据门槛低、行业覆盖有限。对比scraper去爬优质的信息，我写了一个定时任务写在 Docker 里的 cron：每天凌晨两点抓一次，至少保证库里数据是新的；未来如果要接入 Indeed/LinkedIn，只需在 Scraper 容器里加一个“渠道策略”工厂，就能把新源头转成统一 DTO 落库——表结构已经留了 `source` 字段，改动不会太大。

技能抽取这块花的时间最多。一开始只跑了 ``SkillNER + EMSI 词表``，结果发现缺少上下文时命中率挺低，于是加了 TF‑IDF 向量和 SBERT 语义相似度两道保险：先让 ``SkillNER`` 输出候选，再用 SBERT 计算每个候选和技能中心词库的余弦相似度，阈值 0.78 以下直接丢弃；然后把留下来的结果按 TF‑IDF 权重重新排序，写到 `job_skills` 和 `user_skills` 表里。这样做的好处是——即便 Job Description 里写的是 “JS/TS guru”，SkillNER 抓到 “JS”，SBERT 也能把它映射到 “JavaScript” 的 canonical ID，最终算覆盖率时不会漏掉。

简历解析比原先想的很难，直接写parser也没有思路。尝试了一些免费的api，效果也很差；再看商业版收费不低同时接入也很耗时间。权衡后我自己用 ``spaCy`` 加正则写了个轻量解析器：按段落切分，NER 抓 `ORG` 和 `DATE`，正则识别 “B.Sc.”、“Ph.D.” 这些学位标记，再靠时间区间把行文拼起来。

匹配引擎本身不复杂：把用户技能向量和每条工作的技能向量都走一遍 TF‑IDF + Cosine；再根据用户工作年限给分数加权（经验越多，阈值越放宽），排出前 20。最后把 `job_skills - user_skills` 得到差集，按重要度降序展示成“待补技能”，并随手拼接 Coursera 搜索链接，算是学习推荐。这个逻辑先写在 SQLAlchemy Service 层，后面想把它搬到异步任务里缓存——现在数据量小还能实时算，数据一多就得走离线。

前端部分我用 Tailwind + Recharts 做了基本布局：左边侧栏、顶部导航、中央三大块——简历上传、匹配结果、市场趋势。动画效果作为点缀：上传按钮悬停变色、解析时技能气泡加速旋转。Dashboard 的趋势线直接查 `skill_demand_daily`，30 天滚动窗口，Recharts 画线图；Skill Alignment Timeline 读取 `user_skill_history` 按时间点画折线。

未来我想改进的：
1. 寻找更先进的PDF parser，能够通过html元素例如<h2>等区分section，进行skills, experience更精准的填入
2. embed AI model，能够更精准的二次检测skills，education的内容是否准确并进行AI去重。
3. 调查研究看市面上更好的，比如LinkedIn企业级付费API，能够更精准地抓取最新的Job post，与用户的LinkedIn账号绑定，实现更先进的Job Match
4. 引发我思考的一点是，在我自己投递简历的过程中也会遇到一样的问题，目前市面上的根据简历识别skills自动填入的API大多数都不准确，比如我使用的这个job post企业级API也会出现类似情况。例如用户的目标是Software Engineering，他写自己曾经写过User Account Management System,因为这个短句出现的频率过高，所以API会把"user account”也作为skills的一项。我想出的未来解决办法是，接入AI模型，将用户的Education先给AI让它进行处理，处理之后根据Education的内容以及Description进行Skills的筛选。这样会让自动填入的skills更加合理。
