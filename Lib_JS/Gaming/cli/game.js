/**
 * Library:      game.js
 * Family:       Gaming
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL
 * MFDB Version: 1.31
 * Format_Creator: Elton Boehnen
 * Date:         2026-05-18
 * Description:  Game logic controller and level switcher.
 */

import { CoreEngine, ChunkManager } from './lib_bejson_engine_core';
import SwitchRenderer from './lib_bejson_engine_renderer';
import SwitchPhysics from './lib_bejson_physics';
import SwitchInput from './lib_bejson_input';

export class VanillaGame {
    constructor(canvasId, mfdb) {
        this.canvasId = canvasId;
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            console.error("No canvas found with ID " + canvasId);
            return;
        }

        this.mfdb = mfdb;
        this.state = 'TITLE';
        this.score = 0;
        this.dialogText = null;
        this.tileSize = 32;
        this.camera = { x: 0, y: 0, width: 640, height: 480 };

        this.engine = new CoreEngine();
        this.renderer = new SwitchRenderer(canvasId);
        this.physics = new SwitchPhysics();
        this.input = new SwitchInput();

        this.assets = {};
        this.sprites = {};
        this.loadedImages = {};
        this.actors = [];
        this.tiles = [];
        this.player = null;
        this.sword = null;
        
        this.listeners = {};
        
        this.animationFrameId = 0;
        this.lastTime = performance.now();

        this.loop = this.loop.bind(this);
        this.init();
        
        this.animationFrameId = requestAnimationFrame(this.loop);
    }

    on(event, cb) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(cb);
    }

    emit(event, data) {
        if (this.listeners[event]) this.listeners[event].forEach(cb => cb(data));
    }

    notifyPlayerChange() {
        this.emit('onHealthChange', this.player?.health || 0);
        this.emit('UIUpdate');
    }

    init() {
        this.assets = {}; this.sprites = {}; this.loadedImages = {}; this.actors = []; this.tiles = [];
        this.player = null; this.sword = null; this.score = 0;

        const manifest = this.mfdb["104a.mfdb.bejson"];
        const fileOrder = manifest?.Values?.slice().sort((a, b) => a[2] - b[2]) || [];
        const loadedFiles = new Set();
        
        for (const record of fileOrder) {
            const [entity, path, order] = record;
            if (!this.mfdb[path]) continue;
            if (order >= 2 && (!loadedFiles.has("data/object_rules.bejson") || !loadedFiles.has("data/actor_stats.bejson"))) {
                console.error("Dependency error.");
                return;
            }
            loadedFiles.add(path);
        }

        const objectRulesDb = this.mfdb["data/object_rules.bejson"]?.Values || [];
        objectRulesDb.forEach(a => { this.assets[a[0]] = { asset_id: a[0], is_solid: a[1], interactable: a[2], damage: a[3], description: a[4], fallback_color: a[5] }; });
        
        Object.keys(this.mfdb).forEach(filename => {
            if (filename.startsWith("assets/") && filename.endsWith(".bejson")) {
                const fileContent = this.mfdb[filename];
                if (fileContent.Records_Type && fileContent.Records_Type[0].startsWith("Asset") && fileContent.Values && fileContent.Values.length > 0) {
                    const spriteId = fileContent.Asset_Id || filename.split('/').pop().split('.')[0];
                    const dataUri = fileContent.Values[0][0];
                    if (spriteId && dataUri) {
                        this.sprites[spriteId] = dataUri;
                        const img = new Image(); img.src = dataUri; this.loadedImages[spriteId] = img;
                    }
                }
            }
        });
        
        const actorStatsDb = this.mfdb["data/actor_stats.bejson"]?.Values || [];
        const actorStats = {};
        actorStatsDb.forEach(s => { actorStats[s[0]] = { actor_type: s[0], max_health: s[1], atk: s[2], def: s[3], speed: s[4], xp_reward: s[5], fallback_color: s[6], start_potions: s[7] || 0, level_up_hp: s[8] || 0, level_up_atk: s[9] || 0, level_up_def: s[10] || 0 }; });

        const levelDb = this.mfdb["data/level.bejson"]?.Values || [];
        if (levelDb.length > 0) this.level = { id: levelDb[0][0], width: levelDb[0][1], height: levelDb[0][2] }; else return;

        this.engine.initChunking({ basePath: 'data/', chunkSize: 10 * this.tileSize, loadRadius: 1 });

        const actorDb = this.mfdb["data/actor.bejson"]?.Values || [];
        actorDb.forEach(a => {
            const statsConfig = actorStats[a[2]] || { max_health: 50, atk: 5, def: 2, speed: 50, xp_reward: 10, start_potions: 0 };
            const actor = {
                id: a[0], type: a[2], x: a[3] * this.tileSize, y: a[4] * this.tileSize, width: 32, height: 32,
                health: a[5] || statsConfig.max_health, maxHealth: statsConfig.max_health, speed: statsConfig.speed,
                color: statsConfig.fallback_color || '#ffffff', vx: 0, vy: 0, facing: { x: 1, y: 0 },
                atk: a[6] || statsConfig.atk, def: a[7] || statsConfig.def, level: 1, xp: 0, maxXp: 100,
                potions: statsConfig.start_potions || 0, xpReward: statsConfig.xp_reward, levelUpHp: statsConfig.level_up_hp,
                levelUpAtk: statsConfig.level_up_atk, levelUpDef: statsConfig.level_up_def
            };
            if (a[2] === 'player') this.player = actor;
            this.actors.push(actor);
        });

        this.input.update(); // Flush input
    }
    
    destroy() {
        cancelAnimationFrame(this.animationFrameId);
    }
    
    get scoreValue() { return this.score; }
    set scoreValue(v) { this.score = v; this.emit('onScoreUpdate', v); this.emit('UIUpdate'); }
    get stateStatus() { return this.state; }
    set stateStatus(v) { this.state = v; this.emit('onStateChange', v); this.emit('UIUpdate'); }

    serialize() { return JSON.stringify({ score: this.score, player: this.player, actors: this.actors, level: this.level }); }
    deserialize(data) {
        try {
            const parsed = JSON.parse(data); this.scoreValue = parsed.score; this.actors = parsed.actors;
            const playerRef = this.actors.find(a => a.type === 'player');
            if (playerRef) this.player = playerRef; else { this.player = parsed.player; if (this.player) this.actors.push(this.player); }
            this.level = parsed.level; this.stateStatus = 'PLAYING';
        } catch (e) {}
    }

    loop(time) {
        const dt = (time - this.lastTime) / 1000;
        this.lastTime = time;
        if (dt < 0.1) {
            this.update(dt);
            this.draw();
        }
        this.input.update(); // clear just pressed
        this.animationFrameId = requestAnimationFrame(this.loop);
    }

    checkCollision(a, b) { return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y; }

    updateChunksAsync() {
        if (!this.player) return;
        const CHUNK_PIXELS = 10 * this.tileSize;
        const cx = Math.floor(this.player.x / CHUNK_PIXELS);
        const cy = Math.floor(this.player.y / CHUNK_PIXELS);

        const neededChunks = new Set();
        for (let i = -1; i <= 1; i++) {
            for(let j = -1; j <= 1; j++) {
                const nx = cx + i; const ny = cy + j;
                if (nx >= 0 && nx <= 1 && ny >= 0 && ny <= 1) neededChunks.add(`${nx}_${ny}`);
            }
        }

        neededChunks.forEach(chunkKey => {
            if (!this.engine.chunkManager.activeChunks.has(chunkKey) && !this.engine.chunkManager.loadingChunks.has(chunkKey)) {
                this.engine.chunkManager.loadingChunks.add(chunkKey);
                Promise.resolve().then(() => {
                    const [xStr, yStr] = chunkKey.split('_');
                    const file = this.mfdb[`data/tile_chunk_${xStr}_${yStr}.bejson`];
                    if (file) {
                        const newTiles = file.Values.map(t => ({ tile_id: t[0], level_id: t[1], x: t[2], y: t[3], terrain_type: t[4], object_type: t[5], chunkKey }));
                        this.tiles.push(...newTiles);
                    }
                    this.engine.chunkManager.activeChunks.set(chunkKey, file || {});
                    this.engine.chunkManager.loadingChunks.delete(chunkKey);
                });
            }
        });

        const toUnload = Array.from(this.engine.chunkManager.activeChunks.keys()).filter(c => !neededChunks.has(c));
        toUnload.forEach(chunkKey => {
            this.engine.chunkManager.activeChunks.delete(chunkKey);
            this.tiles = this.tiles.filter(t => t.chunkKey !== chunkKey);
        });
    }

    update(dt) {
        const inp = this.input.getVector();

        if (inp.action) {
            if (this.state === 'TITLE') { this.stateStatus = 'PLAYING'; return; }
            if (this.state === 'GAMEOVER' || this.state === 'VICTORY') { this.init(); this.stateStatus = 'PLAYING'; return; }
            if (this.state === 'DIALOG') { this.stateStatus = 'PLAYING'; this.dialogText = null; return; }
            
            if (this.state === 'PLAYING' && !this.sword && this.player) {
                const npc = this.actors.find(a => {
                    if (a.type !== 'npc') return false;
                    const dist = Math.sqrt(Math.pow((a.x + a.width/2) - (this.player.x + this.player.width/2), 2) + Math.pow((a.y + a.height/2) - (this.player.y + this.player.height/2), 2));
                    return dist < 60;
                });
                if (npc) { this.stateStatus = 'DIALOG'; this.dialogText = "Stay safe, brave adventurer. Beyond the rocky path lies great danger... Use 'C' or 'Heal' if your health drops."; }
                else {
                    this.sword = {
                        x: this.player.x + this.player.facing.x * 24, y: this.player.y + this.player.facing.y * 24,
                        width: 48, height: 48, damage: (this.assets['sword'] || {damage: 10}).damage, life: 0.2
                    };
                }
            }
        }

        if (this.input._isBoundJustPressed('menu')) {
            if (this.state === 'PLAYING') { this.stateStatus = 'MENU'; return; }
            else if (this.state === 'MENU' || this.state === 'ITEM_MENU') { this.stateStatus = 'PLAYING'; return; }
        }

        if (this.input.keys['KeyC'] || this.input.keys['KeyR']) {
             if (this.state === 'PLAYING' && this.player && this.player.potions > 0 && this.player.health < this.player.maxHealth) {
                this.player.potions--; this.player.health = Math.min(this.player.maxHealth, this.player.health + 50);
                this.input.keys['KeyC'] = false; // consume it manually
                this.notifyPlayerChange();
             }
        }

        if (this.state !== 'PLAYING' || !this.player || !this.level) return;

        this.updateChunksAsync();

        const levelWidth = this.level.width * this.tileSize; 
        const levelHeight = this.level.height * this.tileSize;

        const checkTileCollision = (actor, vx, vy) => {
            const newX = actor.x + vx * dt; const newY = actor.y + vy * dt;
            for (const tile of this.tiles) {
                const rules = this.assets[tile.terrain_type || tile.object_type];
                if (rules && rules.is_solid && newX < tile.x * this.tileSize + this.tileSize && newX + actor.width > tile.x * this.tileSize && newY < tile.y * this.tileSize + this.tileSize && newY + actor.height > tile.y * this.tileSize) return true;
            }
            return false;
        };

        let pKnockX = 0, pKnockY = 0;
        
        for (let i = this.actors.length - 1; i >= 0; i--) {
            const actor = this.actors[i];
            actor.pendingVx = 0; actor.pendingVy = 0;
            if (actor.type === 'enemy' || actor.type === 'chest') {
                if (actor.type === 'enemy') {
                    const dx = this.player.x - actor.x; const dy = this.player.y - actor.y; const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist > 0 && dist < 300) {
                        actor.pendingVx = (dx / dist) * actor.speed;
                        actor.pendingVy = (dy / dist) * actor.speed;
                    }
                }
                if (this.sword && this.checkCollision(actor, this.sword)) {
                    if (actor.type === 'chest') { this.player.potions++; this.notifyPlayerChange(); this.actors.splice(i, 1); continue; }
                    actor.health -= Math.max(1, this.player.atk - actor.def);
                    actor.pendingVx += this.player.facing.x * 400; 
                    actor.pendingVy += this.player.facing.y * 400;
                    if (actor.health <= 0) {
                        this.actors.splice(i, 1); this.scoreValue += actor.xpReward; this.player.xp += actor.xpReward;
                        if (this.player.xp >= this.player.maxXp) {
                            this.player.level++; this.player.xp -= this.player.maxXp; this.player.maxXp = Math.floor(100 * Math.pow(1.5, this.player.level));
                            this.player.atk += this.player.levelUpAtk || 0; this.player.def += this.player.levelUpDef || 0;
                            this.player.maxHealth += this.player.levelUpHp || 0; this.player.health = this.player.maxHealth;
                        }
                        this.notifyPlayerChange();
                    }
                }
                if (actor.type === 'enemy' && this.checkCollision(actor, this.player)) {
                    if (!this.player.iFrames || this.player.iFrames <= 0) {
                         this.player.health -= Math.max(1, actor.atk - Math.floor(this.player.def / 2)); this.player.iFrames = 1.0;
                         this.notifyPlayerChange();
                         const len = Math.sqrt(Math.pow(this.player.x - actor.x, 2) + Math.pow(this.player.y - actor.y, 2)) || 1;
                         pKnockX += ((this.player.x - actor.x)/len) * 500; 
                         pKnockY += ((this.player.y - actor.y)/len) * 500;
                         if (this.player.health <= 0) this.stateStatus = 'GAMEOVER';
                    }
                }
            }
        }

        let speedMult = 1;
        const currentTile = this.tiles.find(t => t.x === Math.floor((this.player.x + this.player.width/2) / this.tileSize) && t.y === Math.floor((this.player.y + this.player.height/2) / this.tileSize));
        if (currentTile && (currentTile.terrain_type || currentTile.object_type) === 'bush') speedMult = 0.5;
        const currentSpeed = this.player.speed * speedMult;
        
        let targetVx = inp.x;
        let targetVy = inp.y;
        
        let finalVx = targetVx * currentSpeed + pKnockX;
        let finalVy = targetVy * currentSpeed + pKnockY;
        
        let canMoveX = !checkTileCollision(this.player, finalVx, 0);
        let canMoveY = !checkTileCollision(this.player, 0, finalVy);

        if (!canMoveX) { targetVx = 0; finalVx = 0; }
        if (!canMoveY) { targetVy = 0; finalVy = 0; }

        if (targetVx !== 0 && targetVy !== 0) { 
            const length = Math.sqrt(targetVx * targetVx + targetVy * targetVy); 
            finalVx = (targetVx / length) * currentSpeed + pKnockX; 
            finalVy = (targetVy / length) * currentSpeed + pKnockY; 
            if (checkTileCollision(this.player, finalVx, 0)) finalVx = 0;
            if (checkTileCollision(this.player, 0, finalVy)) finalVy = 0;
        }

        this.player.vx = finalVx;
        this.player.vy = finalVy;

        if (targetVx !== 0 || targetVy !== 0) this.player.facing = { x: targetVx === 0 ? 0 : Math.sign(targetVx), y: targetVy === 0 ? 0 : Math.sign(targetVy) };
        
        this.player.x = Math.max(0, Math.min(this.player.x + this.player.vx * dt, levelWidth - this.player.width));
        this.player.y = Math.max(0, Math.min(this.player.y + this.player.vy * dt, levelHeight - this.player.height));
        
        if (this.sword) {
            this.sword.life -= dt;
            this.sword.x = this.player.x + this.player.facing.x * 24; this.sword.y = this.player.y + this.player.facing.y * 24;
            if (this.sword.life <= 0) this.sword = null;
        }
        if (this.player.iFrames > 0) this.player.iFrames -= dt;
        
        for (let i = this.actors.length - 1; i >= 0; i--) {
            const actor = this.actors[i];
            if (actor.type === 'enemy' || actor.type === 'chest') {
                actor.vx = checkTileCollision(actor, actor.pendingVx, 0) ? 0 : actor.pendingVx;
                actor.vy = checkTileCollision(actor, 0, actor.pendingVy) ? 0 : actor.pendingVy;
                actor.x = Math.max(0, Math.min(actor.x + actor.vx * dt, levelWidth - actor.width));
                actor.y = Math.max(0, Math.min(actor.y + actor.vy * dt, levelHeight - actor.height));
            }
        }
        
        if (!this.actors.some(a => a.type === 'enemy')) this.stateStatus = 'VICTORY';
        
        this.camera.x = Math.max(0, Math.min(this.player.x - this.camera.width / 2 + this.player.width / 2, levelWidth - this.camera.width));
        this.camera.y = Math.max(0, Math.min(this.player.y - this.camera.height / 2 + this.player.height / 2, levelHeight - this.camera.height));
        
        this.renderer.camera = { x: this.camera.x, y: this.camera.y, zoom: 1 };
    }

    draw() {
        this.renderer.clear('#0f172a');
        
        if (this.state === 'TITLE' || !this.player || !this.level) return;

        // Draw chunks using Renderer
        const ctx = this.renderer.ctx;
        ctx.save(); 
        const scale = this.renderer.canvas.width / this.camera.width; 
        ctx.scale(scale, scale); 
        ctx.translate(-this.camera.x, -this.camera.y);
        
        // Draw tiles
        this.tiles.forEach(tile => {
            const tx = tile.x * this.tileSize; const ty = tile.y * this.tileSize; const spriteId = tile.terrain_type || tile.object_type;
            if (spriteId) {
                if (this.loadedImages[spriteId] && this.loadedImages[spriteId].complete && this.loadedImages[spriteId].naturalWidth > 0) ctx.drawImage(this.loadedImages[spriteId], tx, ty, this.tileSize, this.tileSize);
                else { ctx.fillStyle = this.assets[spriteId]?.fallback_color || '#000000'; ctx.fillRect(tx, ty, this.tileSize, this.tileSize); }
            }
        });
        
        // Draw actors
        this.actors.forEach(actor => {
            if (actor.type === 'player' && this.player.iFrames > 0 && Math.floor(this.player.iFrames * 10) % 2 === 0) return;
            if (this.loadedImages[actor.type] && this.loadedImages[actor.type].complete && this.loadedImages[actor.type].naturalWidth > 0) ctx.drawImage(this.loadedImages[actor.type], actor.x, actor.y, actor.width, actor.height);
            else { ctx.fillStyle = actor.color; if (actor.type === 'player') { ctx.beginPath(); ctx.arc(actor.x + actor.width/2, actor.y + actor.height/2, actor.width/2, 0, Math.PI*2); ctx.fill(); } else ctx.fillRect(actor.x, actor.y, actor.width, actor.height); }
            if (actor.type === 'enemy' && actor.health < actor.maxHealth) { ctx.fillStyle = 'red'; ctx.fillRect(actor.x, actor.y - 6, actor.width, 4); ctx.fillStyle = 'green'; ctx.fillRect(actor.x, actor.y - 6, actor.width * (actor.health / Math.max(1, actor.maxHealth)), 4); }
        });
        
        // Draw sword
        if (this.sword) {
            if (this.loadedImages['sword'] && this.loadedImages['sword'].complete && this.loadedImages['sword'].naturalWidth > 0) ctx.drawImage(this.loadedImages['sword'], this.sword.x, this.sword.y, this.sword.width, this.sword.height);
            else { ctx.fillStyle = this.assets['sword']?.fallback_color || '#eab308'; ctx.fillRect(this.sword.x, this.sword.y, this.sword.width, this.sword.height); }
        }
        
        ctx.restore();
    }
}
