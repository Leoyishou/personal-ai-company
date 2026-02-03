-- XHS Content Management System Seed Data

-- 1. Insert Series
INSERT INTO xhs_series (id, name, description, content_template, research_template, status, idea_count, published_count)
VALUES (
    'bilibili-up',
    'B站UP主介绍',
    '介绍有深度、有反差的B站UP主',
    '{"style": "反差揭秘", "image_styles": ["线刻肖像", "手绘白板"]}',
    '{"dimensions": ["人设反差", "经典语录", "老粉梗", "隐藏技能"]}',
    'active',
    7,
    1
);

-- 2. Insert Ideas
INSERT INTO xhs_ideas (id, series_id, subject, description, status, priority, tags, metadata) VALUES
('idea_20260202_001', 'bilibili-up', '峰哥亡命天涯', '粗俗外表下的文化深度', 'published', 1, ARRAY['峰哥', '反差', 'B站'], '{"research_id": "research_fenggao"}'),
('idea_20260202_002', 'bilibili-up', '影视飓风 Tim', '技术达人的人文情怀', 'researched', 2, ARRAY['影视飓风', 'Tim', 'B站'], '{"research_id": "research_tim"}'),
('idea_20260202_003', 'bilibili-up', '何同学', '技术博主的文科基因', 'researched', 3, ARRAY['何同学', 'B站'], '{"research_id": "research_hetongxue"}'),
('idea_20260202_004', 'bilibili-up', '无穷小亮', '博物学家的反差萌', 'researched', 4, ARRAY['无穷小亮', 'B站'], '{"research_id": "research_xiaoliang"}'),
('idea_20260202_005', 'bilibili-up', '手工耿', '发明狂人的实用主义', 'researched', 5, ARRAY['手工耿', 'B站'], '{"research_id": "research_geng"}'),
('idea_20260202_006', 'bilibili-up', '极客湾', '理工极客的感性时刻', 'researched', 6, ARRAY['极客湾', 'B站'], '{"research_id": "research_geekerwan"}'),
('idea_20260202_007', 'bilibili-up', '科技美学', '理性测评的感性底色', 'researched', 7, ARRAY['科技美学', 'B站'], '{"research_id": "research_kejimeixue"}');

-- 3. Insert Research Data
INSERT INTO xhs_research (id, idea_id, research_type, content, sources, key_findings, status) VALUES
('research_fenggao', 'idea_20260202_001', 'up_profile', '{
    "name": "峰哥亡命天涯",
    "real_identity": "资深文化人",
    "surface_persona": "油腻大叔、满嘴跑火车",
    "hidden_depth": {
        "bookshelf": ["沉默的大多数-王小波", "黑格尔逻辑学", "资本论", "西方哲学史-罗素", "美的历程-李泽厚"],
        "cultural_references": "能把王小波和黑格尔揉在一起聊",
        "historical_knowledge": "历史典故、哲学梗信手拈来"
    },
    "signature_style": "粗俗是人设，深度藏在细节里",
    "memorable_quotes": ["你以为他在开车，其实他在布道"],
    "fan_memes": ["开车", "下三路", "文化输出"]
}', ARRAY['B站主页', '视频内容分析'], ARRAY['表面油腻实则有深度', '书单惊人', '王小波+黑格尔的混搭'], 'completed'),

('research_tim', 'idea_20260202_002', 'up_profile', '{
    "name": "影视飓风 Tim",
    "real_identity": "技术流影视创作者",
    "surface_persona": "硬核技术党、器材党",
    "hidden_depth": {
        "artistic_side": "镜头语言诗意十足",
        "emotional_works": "《回村三天》等纪录片",
        "philosophy": "技术是为表达服务的"
    },
    "signature_style": "用技术讲人文",
    "memorable_quotes": ["最好的器材是你手里的那一个"],
    "fan_memes": ["器材党", "技术流", "诗意镜头"]
}', ARRAY['B站主页', '纪录片作品'], ARRAY['技术达人有人文情怀', '器材党不迷信器材', '纪录片功底深厚'], 'completed'),

('research_hetongxue', 'idea_20260202_003', 'up_profile', '{
    "name": "何同学",
    "real_identity": "北邮学生/科技博主",
    "surface_persona": "技术宅、数码达人",
    "hidden_depth": {
        "liberal_arts_genes": "传媒学院出身",
        "storytelling": "把技术讲成故事",
        "aesthetic": "极简主义美学"
    },
    "signature_style": "文科生讲理科事",
    "memorable_quotes": ["我不是在测评产品，我是在讲一个故事"],
    "fan_memes": ["何氏转场", "文艺科技", "苹果御用"]
}', ARRAY['B站主页', '采访资料'], ARRAY['传媒背景影响风格', '技术+故事的独特组合', '美学追求极高'], 'completed'),

('research_xiaoliang', 'idea_20260202_004', 'up_profile', '{
    "name": "无穷小亮",
    "real_identity": "博物杂志副主编/博物学家",
    "surface_persona": "严肃科普人",
    "hidden_depth": {
        "humor": "冷面吐槽王",
        "memes": "水猴子、旋转小亮",
        "personality": "反差萌"
    },
    "signature_style": "学术严谨+冷面幽默",
    "memorable_quotes": ["这不是水猴子，这是XXX"],
    "fan_memes": ["水猴子", "鉴定一下", "旋转小亮"]
}', ARRAY['B站主页', '博物杂志'], ARRAY['权威身份+接地气表达', '冷面吐槽成招牌', '科普界的喜剧人'], 'completed'),

('research_geng', 'idea_20260202_005', 'up_profile', '{
    "name": "手工耿",
    "real_identity": "民间发明家/焊工",
    "surface_persona": "发明无用之物",
    "hidden_depth": {
        "practicality": "很多发明其实有用",
        "craftsmanship": "焊接技术一流",
        "philosophy": "用无用之用对抗内卷"
    },
    "signature_style": "看似无用，实则有趣",
    "memorable_quotes": ["有用的东西太多了，我做点没用的"],
    "fan_memes": ["没用发明家", "焊武帝", "保定爱迪生"]
}', ARRAY['B站主页', '采访资料'], ARRAY['无用是一种态度', '手艺人精神', '对抗功利主义的行为艺术'], 'completed'),

('research_geekerwan', 'idea_20260202_006', 'up_profile', '{
    "name": "极客湾",
    "real_identity": "硬核科技测评团队",
    "surface_persona": "数据党、理工男",
    "hidden_depth": {
        "emotional_moments": "偶尔的感性评价",
        "aesthetic": "对产品设计的欣赏",
        "values": "不只看参数，也看体验"
    },
    "signature_style": "数据之外有温度",
    "memorable_quotes": ["数据不会骗人，但数据也不是全部"],
    "fan_memes": ["跑分狂魔", "图表战神", "理性测评"]
}', ARRAY['B站主页', '测评视频'], ARRAY['硬核团队也有感性面', '数据+体验双重视角', '理工男的审美觉醒'], 'completed'),

('research_kejimeixue', 'idea_20260202_007', 'up_profile', '{
    "name": "科技美学",
    "real_identity": "科技测评博主",
    "surface_persona": "理性测评人",
    "hidden_depth": {
        "emotional_side": "对品牌故事的感性理解",
        "design_appreciation": "深入产品设计语言",
        "values": "科技应该有温度"
    },
    "signature_style": "美学角度看科技",
    "memorable_quotes": ["科技产品也是艺术品"],
    "fan_memes": ["美学测评", "感性派", "设计控"]
}', ARRAY['B站主页', '测评视频'], ARRAY['测评中的美学视角', '品牌故事讲述者', '科技+人文的融合'], 'completed');

-- 4. Insert Copy (for published content)
INSERT INTO xhs_copies (id, idea_id, title, body, version, is_valid) VALUES
('copy_20260202_001', 'idea_20260202_001', '三句不离下三路的峰哥，书单吓你一跳',
'你以为峰哥只会开车？

那个满嘴跑火车、三句话不离下三路的油腻大叔，书架上摆的是：

《沉默的大多数》王小波
《黑格尔逻辑学》
《资本论》
《西方哲学史》罗素
《美的历程》李泽厚

一个能把王小波和黑格尔揉在一起聊的人，怎么可能只是个"开车的"？

粗俗是人设，深度藏在细节里。那些看似不经意的历史典故、哲学梗，不是临时百度的。

你以为他在开车，其实他在布道。',
1, true);

-- 5. Insert Images
INSERT INTO xhs_images (id, idea_id, path, style, role, generation_prompt, source_type) VALUES
('img_20260202_001', 'idea_20260202_001', '~/.claude/Nanobanana-draw-图片/20260202_线刻肖像_峰哥v2_0.jpg', '线刻肖像', 'cover', '将照片转换为黑白线刻风格...', 'generated'),
('img_20260202_002', 'idea_20260202_001', '~/.claude/Nanobanana-draw-图片/20260202_手绘白板_峰哥书单_0.png', '手绘白板', 'detail', NULL, 'generated');

-- 6. Insert Publication
INSERT INTO xhs_publications (id, idea_id, copy_id, platform, published_at, snapshot, publisher) VALUES
('d0000001-aaaa-bbbb-cccc-000000000001', 'idea_20260202_001', 'copy_20260202_001', 'xiaohongshu', '2026-02-02T15:30:00+08:00',
'{
    "title": "三句不离下三路的峰哥，书单吓你一跳",
    "body": "你以为峰哥只会开车？\n\n那个满嘴跑火车、三句话不离下三路的油腻大叔，书架上摆的是：\n\n《沉默的大多数》王小波\n《黑格尔逻辑学》\n《资本论》\n《西方哲学史》罗素\n《美的历程》李泽厚\n\n一个能把王小波和黑格尔揉在一起聊的人，怎么可能只是个\"开车的\"？\n\n粗俗是人设，深度藏在细节里。那些看似不经意的历史典故、哲学梗，不是临时百度的。\n\n你以为他在开车，其实他在布道。",
    "tags": ["峰哥亡命天涯", "B站宝藏UP主", "被低估的文化人", "反差感", "王小波"],
    "images": ["~/.claude/Nanobanana-draw-图片/20260202_线刻肖像_峰哥v2_0.jpg", "~/.claude/Nanobanana-draw-图片/20260202_手绘白板_峰哥书单_0.png"]
}',
'assistant');

-- 7. Insert Evaluation
INSERT INTO xhs_evaluations (id, publication_id, metrics, tracking_status) VALUES
('eval_20260202_001', 'd0000001-aaaa-bbbb-cccc-000000000001',
'{
    "D0": {"recorded_at": "2026-02-02T15:30:00+08:00", "likes": 0, "comments": 0, "collects": 0, "views": 0},
    "D1": null,
    "D7": null,
    "D30": null
}',
'{
    "D1_due": "2026-02-03T15:30:00+08:00",
    "D1_done": false,
    "D7_due": "2026-02-09T15:30:00+08:00",
    "D7_done": false,
    "D30_due": "2026-03-04T15:30:00+08:00",
    "D30_done": false
}');
