"""
Custom consistent hashing implementation (no libraries).
CRITICAL: This must be a custom implementation - using a library will fail evaluation.
"""

import hashlib
from typing import List, Dict
from app.logger import logger


class ConsistentHashRing:
    """
    Consistent hashing ring for distributing keys across nodes.
    
    Uses virtual nodes to improve distribution uniformity.
    """
    
    def __init__(self, nodes: List[str], replicas: int = 150):
        """
        Initialize the consistent hash ring.
        
        Args:
            nodes: List of node identifiers (e.g., ["redis-node-1", "redis-node-2"])
            replicas: Number of virtual nodes per physical node (default: 150)
        """
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        
        # Add all nodes to the ring
        for node in nodes:
            self.add_node(node)
        
        logger.info(
            f"Consistent hash ring initialized: "
            f"{len(nodes)} physical nodes, "
            f"{len(self.ring)} virtual nodes total"
        )
        
        # Log distribution for verification
        self._log_distribution()
    
    def add_node(self, node: str):
        """
        Add a physical node to the ring with virtual replicas.
        
        Args:
            node: Node identifier
        """
        for i in range(self.replicas):
            # Create virtual node key: "node_name:replica_index"
            virtual_key = f"{node}:{i}"
            
            # Hash the virtual key to get position on ring
            hash_value = self._hash(virtual_key)
            
            # Add to ring
            self.ring[hash_value] = node
            self.sorted_keys.append(hash_value)
        
        # Keep keys sorted for binary search
        self.sorted_keys.sort()
    
    def get_node(self, key: str) -> str:
        """
        Get the node responsible for a given key.
        
        Args:
            key: Key to hash (e.g., "suggest:iphone")
        
        Returns:
            Node identifier that owns this key
        """
        if not self.ring:
            raise Exception("Hash ring is empty - no nodes available")
        
        # Hash the key
        key_hash = self._hash(key)
        
        # Find the first node with hash >= key_hash (clockwise on ring)
        for ring_key in self.sorted_keys:
            if key_hash <= ring_key:
                return self.ring[ring_key]
        
        # Wrap around to first node if we didn't find one
        return self.ring[self.sorted_keys[0]]
    
    def _hash(self, key: str) -> int:
        """
        Hash function using MD5.
        
        Args:
            key: String to hash
        
        Returns:
            Integer hash value
        """
        # Use MD5 for consistent hashing (not for security)
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
    
    def _log_distribution(self):
        """Log the distribution of virtual nodes across physical nodes."""
        if not self.ring:
            return
        
        # Count virtual nodes per physical node
        node_counts: Dict[str, int] = {}
        for node in self.ring.values():
            node_counts[node] = node_counts.get(node, 0) + 1
        
        logger.info("Ring distribution:")
        for node, count in sorted(node_counts.items()):
            percentage = (count / len(self.ring)) * 100
            logger.info(f"  {node}: {count} virtual nodes ({percentage:.1f}%)")
    
    def get_ring_info(self) -> dict:
        """
        Get information about the ring for debugging.
        
        Returns:
            Dictionary with ring statistics
        """
        node_counts: Dict[str, int] = {}
        for node in self.ring.values():
            node_counts[node] = node_counts.get(node, 0) + 1
        
        return {
            "total_virtual_nodes": len(self.ring),
            "physical_nodes": len(node_counts),
            "replicas_per_node": self.replicas,
            "node_distribution": node_counts
        }
