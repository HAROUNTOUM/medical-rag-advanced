

class Node(BaseNode):
    id: str =  (..., description="Name or human-readable unique identifier")
    label: str = Field(..., description=f"Available options are {enum_values}")
    properties: Optional[List[Property]]
class Relationship(BaseRelationship):
    source_node_id: str
    source_node_label: str = Field(..., description=f"Available options are {enum_values}")
    target_node_id: str
    target_node_label: str = Field(..., description=f"Available options are {enum_values}")
    type: str = Field(..., description=f"Available options are {enum_values}")
    properties: Optional[List[Property]]
class KnowledgeGraph(BaseModel):
    nodes:list[Node]= Field(...,description="List of nodes" )
    relationships:list[Relationship]= Field(...,description="List of relationships")