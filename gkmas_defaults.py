from __future__ import annotations

DEFAULT_CHARACTERS = {
    "characters": [
        {"id": "saki", "name_full": "花海咲季", "name_short": "咲季", "aliases": ["hsak", "saki", "咲季", "花海咲季"], "image": "assets/characters/saki.png", "color": "#F58F92"},
        {"id": "tmr", "name_full": "月村手毬", "name_short": "手毬", "aliases": ["temari", "tmr", "手毬", "手球", "月村手毬"], "image": "assets/characters/tmr.png", "color": "#BFDDF4"},
        {"id": "ktn", "name_full": "藤田ことね", "name_short": "ことね", "aliases": ["kotone", "ktn", "ことね", "藤田ことね"], "image": "assets/characters/ktn.png", "color": "#F4F76D"},
        {"id": "mao", "name_full": "有村麻央", "name_short": "麻央", "aliases": ["mao", "麻央", "有村麻央"], "image": "assets/characters/mao.png", "color": "#E47ADC"},
        {"id": "lly", "name_full": "葛城リーリヤ", "name_short": "リーリヤ", "aliases": ["lilja", "lly", "リーリヤ", "葛城リーリヤ"], "image": "assets/characters/lly.png", "color": "#EAFBFF"},
        {"id": "china", "name_full": "倉本千奈", "name_short": "千奈", "aliases": ["china", "chn", "千奈", "倉本千奈"], "image": "assets/characters/china.png", "color": "#F6A24B"},
        {"id": "smk", "name_full": "紫雲清夏", "name_short": "清夏", "aliases": ["sumika", "smk", "清夏", "紫雲清夏"], "image": "assets/characters/smk.png", "color": "#8AF346"},
        {"id": "hiro", "name_full": "篠澤広", "name_short": "広", "aliases": ["hiro", "hr", "広", "篠澤広"], "image": "assets/characters/hiro.png", "color": "#45C4D0"},
        {"id": "rinami", "name_full": "姫崎莉波", "name_short": "莉波", "aliases": ["rinami", "rnm", "莉波", "姫崎莉波"], "image": "assets/characters/rinami.png", "color": "#F3B7C8"},
        {"id": "ume", "name_full": "花海佑芽", "name_short": "佑芽", "aliases": ["ume", "佑芽", "花海佑芽"], "image": "assets/characters/ume.png", "color": "#F47E62"},
        {"id": "misuzu", "name_full": "秦谷美鈴", "name_short": "美鈴", "aliases": ["misuzu", "msz", "美鈴", "秦谷美鈴"], "image": "assets/characters/misuzu.png", "color": "#9EB0D2"},
        {"id": "sena", "name_full": "十王星南", "name_short": "星南", "aliases": ["sena", "星南", "十王星南"], "image": "assets/characters/sena.png", "color": "#F5C46D"},
        {"id": "tsubame", "name_full": "？？燦", "name_short": "燦", "aliases": ["tsubame", "燦"], "image": "assets/characters/tsubame.png", "color": "#8E82E5"},
        {"id": "asari", "name_full": "？？あさり", "name_short": "あさり", "aliases": ["asari", "あさり"], "image": "assets/characters/asari.png", "color": "#A3DCBD"},
        {"id": "kunio", "name_full": "？？邦夫", "name_short": "邦夫", "aliases": ["kunio", "邦夫"], "image": "assets/characters/kunio.png", "color": "#F4A12F"},
        {"id": "yu", "name_full": "？？優", "name_short": "優", "aliases": ["yu", "優"], "image": "assets/characters/yu.png", "color": "#8E8BE8"},
        {"id": "toha", "name_full": "？？燈羽", "name_short": "燈羽", "aliases": ["toha", "燈羽"], "image": "assets/characters/toha.png", "color": "#77639E"},
        {"id": "nadeshiko", "name_full": "？？撫子", "name_short": "撫子", "aliases": ["nadeshiko", "撫子"], "image": "assets/characters/nadeshiko.png", "color": "#F5A7F2"},
    ]
}

DEFAULT_GROUPS = {
    "groups": [
        {"id": "hatsuboshi", "name": "初星全员", "aliases": ["初星", "初星全員", "all", "allstars"], "expression": "saki+tmr+ktn+mao+lly+china+smk+hiro+rinami"},
        {"id": "group_s", "name": "组合S", "aliases": ["groupS", "s组", "S组"], "expression": "saki+tmr+ktn"},
        {"id": "support", "name": "支援组", "aliases": ["supporters", "支援"], "expression": "ume+misuzu+sena"},
    ]
}

DEFAULT_DAILY_IDOL_CONFIG = {
    "group": "hatsuboshi"
}
