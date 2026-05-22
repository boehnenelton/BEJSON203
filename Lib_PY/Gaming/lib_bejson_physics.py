"""
Library:      lib_bejson_physics.py
Family:       Gaming
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.1.0 OFFICIAL (Simulation Parity)
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-22
Description:  2D/3D physics calculation engine for BEJSON-based simulations.
REMEDIATED:   Synchronized friction (0.9) and restitution with bejson_physics.ts.
"""

import math

class BEJSONPhysics:
    """
    Mirror of lib_bejson_physics.js
    Python/Flask-compatible 2D physics engine using BEJSON 104.
    """
    def __init__(self, world_name="PhysicsWorld"):
        self.bejson = {
            "Format": "BEJSON",
            "Format_Creator": "Elton Boehnen",
            "Format_Version": "104",
            "Records_Type": ["Body"],
            "Fields": [
                { "name": "id", "type": "string" },
                { "name": "x", "type": "number" },
                { "name": "y", "type": "number" },
                { "name": "width", "type": "number" },
                { "name": "height", "type": "number" },
                { "name": "vx", "type": "number" },
                { "name": "vy", "type": "number" },
                { "name": "mass", "type": "number" },
                { "name": "isStatic", "type": "boolean" },
                { "name": "groups", "type": "array" }
            ],
            "Values": []
        }
        self.gravity = {"x": 0, "y": 9.8}
        self.friction = 0.9  # Parity with bejson_physics.ts
        self.restitution = 0.8 # Energy loss on collision

    def add_body(self, body_id, x, y, width, height, **options):
        vx = options.get("vx", 0)
        vy = options.get("vy", 0)
        mass = options.get("mass", 1)
        is_static = options.get("isStatic", False)
        groups = options.get("groups", ["default"])
        
        self.bejson["Values"].append([
            body_id, x, y, width, height, vx, vy, mass, is_static, groups
        ])

    def step(self, dt):
        values = self.bejson["Values"]
        # 1. Integration
        for row in values:
            if row[8]: # isStatic
                continue
            
            # Apply friction to current velocity
            row[5] *= self.friction
            row[6] *= self.friction
            
            # Apply gravity
            row[5] += self.gravity["x"] * dt # vx
            row[6] += self.gravity["y"] * dt # vy
            
            # Apply velocity to position
            row[1] += row[5] * dt # x
            row[2] += row[6] * dt # y

        # 2. Collision Resolution
        for i in range(len(values)):
            body_a = values[i]
            for j in range(i + 1, len(values)):
                body_b = values[j]
                if self._check_aabb(body_a, body_b):
                    self._resolve_collision(body_a, body_b)

    def _check_aabb(self, a, b):
        return (a[1] < b[1] + b[3] and 
                a[1] + a[3] > b[1] and 
                a[2] < b[2] + b[4] and 
                a[2] + a[4] > b[2])

    def _resolve_collision(self, a, b):
        if a[8] and b[8]: return
        
        # Advanced Resolution: Elastic collision with restitution
        # For dynamic-static or dynamic-dynamic
        if a[8]: # a is static
            b[5] *= -self.restitution
            b[6] *= -self.restitution
        elif b[8]: # b is static
            a[5] *= -self.restitution
            a[6] *= -self.restitution
        else:
            # Simple momentum exchange for dynamic-dynamic
            m_a, m_b = a[7], b[7]
            temp_vx_a, temp_vy_a = a[5], a[6]
            
            # v' = (v1(m1-m2) + 2*m2*v2) / (m1+m2)
            a[5] = (temp_vx_a * (m_a - m_b) + 2 * m_b * b[5]) / (m_a + m_b) * self.restitution
            a[6] = (temp_vy_a * (m_a - m_b) + 2 * m_b * b[6]) / (m_a + m_b) * self.restitution
            
            b[5] = (b[5] * (m_b - m_a) + 2 * m_a * temp_vx_a) / (m_a + m_b) * self.restitution
            b[6] = (b[6] * (m_b - m_a) + 2 * m_a * temp_vy_a) / (m_a + m_b) * self.restitution

    def export_bejson(self):
        import json
        return json.dumps(self.bejson, indent=2)

