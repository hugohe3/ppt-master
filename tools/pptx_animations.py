#!/usr/bin/env python3
"""
PPT Master - PPTX 动画模块

提供幻灯片切换效果和入场动画的 XML 生成功能。

支持的切换效果:
    - fade: 淡入淡出
    - push: 推入
    - wipe: 擦除
    - split: 分割
    - reveal: 揭示
    - random: 随机

支持的入场动画:
    - fade: 淡入
    - fly: 飞入
    - zoom: 缩放
    - appear: 出现

依赖: 无（纯 XML 生成）
"""

from typing import Optional, Dict, Any


# ============================================================================
# 切换效果定义
# ============================================================================

TRANSITIONS: Dict[str, Dict[str, Any]] = {
    'fade': {
        'name': '淡入淡出',
        'element': 'fade',
        'attrs': {},
    },
    'push': {
        'name': '推入',
        'element': 'push',
        'attrs': {'dir': 'r'},  # 从右侧推入
    },
    'wipe': {
        'name': '擦除',
        'element': 'wipe',
        'attrs': {'dir': 'r'},  # 从右侧擦除
    },
    'split': {
        'name': '分割',
        'element': 'split',
        'attrs': {'orient': 'horz', 'dir': 'out'},
    },
    'reveal': {
        'name': '揭示',
        'element': 'strips',
        'attrs': {'dir': 'rd'},  # 右下角揭示
    },
    'cover': {
        'name': '覆盖',
        'element': 'cover',
        'attrs': {'dir': 'r'},
    },
    'random': {
        'name': '随机',
        'element': 'random',
        'attrs': {},
    },
}

# 速度映射 (秒 -> OOXML 速度值)
SPEED_MAP = {
    'slow': 1.0,
    'med': 0.5,
    'fast': 0.25,
}


def duration_to_speed(duration: float) -> str:
    """将持续时间（秒）转换为 OOXML 速度值"""
    if duration >= 0.75:
        return 'slow'
    elif duration >= 0.35:
        return 'med'
    else:
        return 'fast'


def create_transition_xml(
    effect: str = 'fade',
    duration: float = 0.5,
    advance_after: Optional[float] = None
) -> str:
    """
    生成幻灯片切换效果 XML 片段
    
    Args:
        effect: 切换效果名称 (fade/push/wipe/split/reveal/cover/random)
        duration: 切换持续时间（秒）
        advance_after: 自动翻页间隔（秒），None 表示手动翻页
    
    Returns:
        可插入 slide XML 的 <p:transition> 元素字符串
    """
    if effect not in TRANSITIONS:
        effect = 'fade'
    
    trans_info = TRANSITIONS[effect]
    element_name = trans_info['element']
    attrs = trans_info['attrs']
    
    # 构建速度属性
    speed = duration_to_speed(duration)
    
    # 构建自动翻页属性
    adv_attr = ''
    if advance_after is not None:
        adv_tm = int(advance_after * 1000)  # 转换为毫秒
        adv_attr = f' advTm="{adv_tm}"'
    
    # 构建效果元素属性
    effect_attrs = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
    if effect_attrs:
        effect_attrs = ' ' + effect_attrs
    
    # 生成 XML
    return f'''  <p:transition spd="{speed}"{adv_attr}>
    <p:{element_name}{effect_attrs}/>
  </p:transition>'''


# ============================================================================
# 入场动画定义
# ============================================================================

ANIMATIONS: Dict[str, Dict[str, Any]] = {
    'fade': {
        'name': '淡入',
        'filter': 'fade',
    },
    'fly': {
        'name': '飞入',
        'filter': 'fly',
        'prLst': 'from(b)',  # 从底部飞入
    },
    'zoom': {
        'name': '缩放',
        'filter': 'zoom',
        'prLst': 'in',
    },
    'appear': {
        'name': '出现',
        'filter': None,  # 无滤镜，仅设置可见性
    },
}


def create_timing_xml(
    animation: str = 'fade',
    duration: float = 1.0,
    delay: float = 0,
    shape_id: int = 2
) -> str:
    """
    生成入场动画 timing XML 片段
    
    Args:
        animation: 动画效果名称 (fade/fly/zoom/appear)
        duration: 动画持续时间（秒）
        delay: 动画延迟（秒）
        shape_id: 目标形状 ID（SVG 图片通常为 2）
    
    Returns:
        可插入 slide XML 的 <p:timing> 元素字符串
    """
    if animation not in ANIMATIONS:
        animation = 'fade'
    
    anim_info = ANIMATIONS[animation]
    dur_ms = int(duration * 1000)
    delay_ms = int(delay * 1000)
    
    # 根据动画类型生成不同的效果 XML
    if anim_info['filter'] is None:
        # appear 动画：仅设置可见性
        effect_xml = f'''                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="5" dur="1" fill="hold">
                                  <p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst>
                                </p:cTn>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                              </p:cBhvr>
                              <p:to><p:strVal val="visible"/></p:to>
                            </p:set>'''
    else:
        # 其他动画：设置可见性 + 动画效果
        filter_name = anim_info['filter']
        pr_attr = ''
        if 'prLst' in anim_info:
            pr_attr = f' prLst="{anim_info["prLst"]}"'
        
        effect_xml = f'''                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="5" dur="1" fill="hold">
                                  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                                </p:cTn>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                              </p:cBhvr>
                              <p:to><p:strVal val="visible"/></p:to>
                            </p:set>
                            <p:animEffect transition="in" filter="{filter_name}"{pr_attr}>
                              <p:cBhvr>
                                <p:cTn id="6" dur="{dur_ms}"/>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                              </p:cBhvr>
                            </p:animEffect>'''
    
    return f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" nodeType="tmRoot">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="seek">
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="3" fill="hold">
                      <p:stCondLst>
                        <p:cond delay="{delay_ms}"/>
                      </p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="4" fill="hold">
                            <p:childTnLst>
{effect_xml}
                            </p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
            </p:seq>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>'''


def get_available_transitions() -> list:
    """获取所有可用的切换效果列表"""
    return list(TRANSITIONS.keys())


def get_available_animations() -> list:
    """获取所有可用的入场动画列表"""
    return list(ANIMATIONS.keys())


def get_transition_help() -> str:
    """获取切换效果帮助文本"""
    lines = ["可用的切换效果:"]
    for key, info in TRANSITIONS.items():
        lines.append(f"  {key}: {info['name']}")
    return '\n'.join(lines)


def get_animation_help() -> str:
    """获取入场动画帮助文本"""
    lines = ["可用的入场动画:"]
    for key, info in ANIMATIONS.items():
        lines.append(f"  {key}: {info['name']}")
    return '\n'.join(lines)


if __name__ == '__main__':
    # 测试输出
    print("=== 切换效果 XML 示例 (fade) ===")
    print(create_transition_xml('fade', 0.5))
    print()
    print("=== 入场动画 XML 示例 (fade) ===")
    print(create_timing_xml('fade', 1.0))
