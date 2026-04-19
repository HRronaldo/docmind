"""
知识图谱模块
============

提供实体关系抽取和图构建功能。

功能：
- 实体识别（基于术语识别）
- 关系抽取（基于共现）
- 内存图构建
- 图查询

Usage:
```python
from app.nlp.kg import KnowledgeGraph, extract_entities_relations

# 简单用法
graph = extract_entities_relations("深度学习由神经网络组成，PyTorch是Facebook开发的框架")
print(graph)

# 高级用法
kg = KnowledgeGraph()
kg.add_text("BERT是Google开发的模型...")
kg.add_text("Transformer由Google提出...")
entities = kg.get_entities()
relations = kg.get_relations()
```
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from app.nlp.terms import TermRecognizer
from app.nlp.segmenter import segment_text
from app.core.logger import get_logger

logger = get_logger("docmind.nlp.kg")


class KnowledgeGraph:
    """
    知识图谱

    基于内存的简单图结构，支持：
    - 添加文本（自动提取实体和关系）
    - 查询实体
    - 查询关系
    - 查找实体邻居
    """

    def __init__(self):
        """初始化图谱"""
        # 实体: {id: {label, type, mentions}}
        self.entities: Dict[str, Dict] = {}
        
        # 关系: [(source_id, target_id, relation_type)]
        self.relations: List[Tuple[str, str, str]] = []
        
        # 术语识别器
        self.recognizer = TermRecognizer()
        
        # 统计
        self.entity_counter = 0
        
        logger.debug("KnowledgeGraph initialized")

    def _get_entity_id(self, entity_label: str, entity_type: str) -> str:
        """获取或创建实体 ID"""
        key = f"{entity_type}:{entity_label}"
        
        if key not in self.entities:
            self.entity_counter += 1
            self.entities[key] = {
                "id": self.entity_counter,
                "label": entity_label,
                "type": entity_type,
                "mentions": 0,
            }
        
        self.entities[key]["mentions"] += 1
        return key

    def add_text(self, text: str, relation_extraction: bool = True) -> Dict:
        """
        添加文本到图谱

        Args:
            text: 输入文本
            relation_extraction: 是否提取关系

        Returns:
            提取结果
        """
        if not text:
            return {"entities": 0, "relations": 0}

        # 1. 提取实体
        terms = self.recognizer.recognize(text)
        
        # 2. 添加实体到图谱
        entity_ids = []
        for term_info in terms:
            entity_id = self._get_entity_id(
                term_info["term"], 
                term_info["type"]
            )
            entity_ids.append(entity_id)

        # 3. 提取关系（基于共现）
        added_relations = 0
        if relation_extraction and len(entity_ids) > 1:
            for i in range(len(entity_ids)):
                for j in range(i + 1, len(entity_ids)):
                    # 检查关系是否已存在
                    if (entity_ids[i], entity_ids[j], "co-occur") not in self.relations and \
                       (entity_ids[j], entity_ids[i], "co-occur") not in self.relations:
                        self.relations.append((entity_ids[i], entity_ids[j], "co-occur"))
                        added_relations += 1

        result = {
            "entities": len(entity_ids),
            "relations": added_relations,
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
        }
        
        logger.debug(f"Added text: {result}")
        return result

    def get_entities(self, entity_type: Optional[str] = None) -> List[Dict]:
        """
        获取实体列表

        Args:
            entity_type: 过滤类型

        Returns:
            实体列表
        """
        entities = []
        
        for key, entity in self.entities.items():
            if entity_type is None or entity["type"] == entity_type:
                entities.append({
                    "id": key,
                    "label": entity["label"],
                    "type": entity["type"],
                    "mentions": entity["mentions"],
                })
        
        # 按提及次数排序
        entities.sort(key=lambda x: -x["mentions"])
        return entities

    def get_relations(self, entity_id: Optional[str] = None) -> List[Dict]:
        """
        获取关系列表

        Args:
            entity_id: 可选的实体过滤

        Returns:
            关系列表
        """
        relations = []
        
        for source_id, target_id, rel_type in self.relations:
            if entity_id is None or source_id == entity_id or target_id == entity_id:
                source = self.entities.get(source_id, {})
                target = self.entities.get(target_id, {})
                
                relations.append({
                    "source": source.get("label", ""),
                    "target": target.get("label", ""),
                    "type": rel_type,
                })
        
        return relations

    def get_neighbors(self, entity_label: str) -> List[Dict]:
        """
        获取实体邻居

        Args:
            entity_label: 实体标签

        Returns:
            邻居列表
        """
        neighbors = []
        
        # 找到实体 ID
        entity_id = None
        for key, entity in self.entities.items():
            if entity["label"] == entity_label:
                entity_id = key
                break
        
        if not entity_id:
            return []

        # 找到相关关系
        for source_id, target_id, rel_type in self.relations:
            if source_id == entity_id:
                target = self.entities.get(target_id, {})
                neighbors.append({
                    "label": target.get("label", ""),
                    "type": target.get("type", ""),
                    "relation": rel_type,
                    "direction": "outgoing",
                })
            elif target_id == entity_id:
                source = self.entities.get(source_id, {})
                neighbors.append({
                    "label": source.get("label", ""),
                    "type": source.get("type", ""),
                    "relation": rel_type,
                    "direction": "incoming",
                })

        return neighbors

    def query(self, entity_label: str) -> Dict:
        """
        查询实体信息

        Args:
            entity_label: 实体标签

        Returns:
            实体详情
        """
        # 查找实体
        entity = None
        for key, e in self.entities.items():
            if e["label"] == entity_label:
                entity = e
                key_id = key
                break

        if not entity:
            return {"found": False}

        # 获取邻居
        neighbors = self.get_neighbors(entity_label)

        return {
            "found": True,
            "label": entity["label"],
            "type": entity["type"],
            "mentions": entity["mentions"],
            "neighbors": neighbors,
        }

    def to_dict(self) -> Dict:
        """
        导出图谱为字典

        Returns:
            图谱数据
        """
        return {
            "entities": self.get_entities(),
            "relations": self.get_relations(),
            "stats": {
                "total_entities": len(self.entities),
                "total_relations": len(self.relations),
            },
        }

    def clear(self):
        """清空图谱"""
        self.entities.clear()
        self.relations.clear()
        self.entity_counter = 0
        logger.debug("KnowledgeGraph cleared")


def extract_entities_relations(
    text: str,
    relation_extraction: bool = True
) -> Dict:
    """
    便捷函数：从文本提取实体和关系

    Args:
        text: 输入文本
        relation_extraction: 是否提取关系

    Returns:
        图谱数据

    Examples:
        >>> result = extract_entities_relations("深度学习由神经网络组成，PyTorch是Facebook开发的框架")
        >>> print(result['entities'])
        [{'label': '深度学习', 'type': 'tech', ...}, ...]
    """
    kg = KnowledgeGraph()
    kg.add_text(text, relation_extraction=relation_extraction)
    return kg.to_dict()


def build_graph_from_texts(texts: List[str]) -> Dict:
    """
    从多个文本构建图谱

    Args:
        texts: 文本列表

    Returns:
        图谱数据
    """
    kg = KnowledgeGraph()
    
    for text in texts:
        kg.add_text(text)
    
    return kg.to_dict()