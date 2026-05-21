"""
Library:      lib_cms_mfdb.py
Family:       CMS
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Relational database layer for CMS content, pages, and taxonomies.
"""

import os
import sys
import uuid
import hashlib
import shutil
import re
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add Lib to path
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

import lib_bejson_core as BEJSONCore
import lib_mfdb_core as MFDBCore

class MFDB_CMS_Manager:
    def __init__(self, data_root: str):
        self.data_root = data_root
        self.workspace_root = os.path.join(data_root, "workspace")
        self.global_db_root = os.path.join(self.workspace_root, "db_global")
        self.content_db_root = os.path.join(self.workspace_root, "db_content")
        self.assets_dir = os.path.join(data_root, "assets")
        self.apps_dir = os.path.join(data_root, "standalone_apps")
        self.www_root = os.path.join(os.path.dirname(data_root), "Processing", "www")
        
        # Manifests inside the workspace
        self.global_manifest = os.path.join(self.global_db_root, "104a.mfdb.bejson")
        self.content_manifest = os.path.join(self.content_db_root, "104a.mfdb.bejson")
        
        # Transport Archives (Source of truth)
        self.global_archive = os.path.join(data_root, "global_master.mfdb.zip")
        self.content_archive = os.path.join(data_root, "content_master.mfdb.zip")

        self.is_dirty = False
        
        if not os.path.exists(self.assets_dir): os.makedirs(self.assets_dir)
        if not os.path.exists(self.apps_dir): os.makedirs(self.apps_dir)

    def set_dirty(self):
        self.is_dirty = True

    def clear_dirty(self):
        self.is_dirty = False

    def mount_system(self, force: bool = False):
        """Mount source archives into the workspace."""
        if not os.path.exists(self.global_archive) or not os.path.exists(self.content_archive):
            # Initial setup if archives don't exist
            if not os.path.exists(self.global_db_root): os.makedirs(self.global_db_root)
            if not os.path.exists(self.content_db_root): os.makedirs(self.content_db_root)
            self.initialize_system()
            
            # Create dummy locks so repack doesn't fail on first run
            for db_root in [self.global_db_root, self.content_db_root]:
                lock_file = os.path.join(db_root, ".mfdb_lock")
                if not os.path.exists(lock_file):
                    with open(lock_file, "w") as f:
                        json.dump({"pid": os.getpid(), "mounted_at": "initial_setup"}, f)

            # Create initial archives from fresh system
            self.repack_system()
            return

        MFDBCore.MFDBArchive.mount(self.global_archive, self.global_db_root, force=force)
        MFDBCore.MFDBArchive.mount(self.content_archive, self.content_db_root, force=force)
        self.clear_dirty()

    def repack_system(self):
        """Commit workspace changes back to transport archives."""
        MFDBCore.MFDBArchive.commit(self.global_db_root, self.global_archive)
        MFDBCore.MFDBArchive.commit(self.content_db_root, self.content_archive)
        self.clear_dirty()

    def factory_reset(self):
        """Wipes all databases, assets, and generated site content."""
        dirs_to_wipe = [self.workspace_root, self.assets_dir, self.apps_dir, self.www_root]
        for d in dirs_to_wipe:
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d)
        # Remove archives
        for arc in [self.global_archive, self.content_archive]:
            if os.path.exists(arc): os.remove(arc)
            
        print("Factory reset complete. System wiped.")

    def initialize_system(self):
        """Initialize both global and content databases if they don't exist."""
        
        # 1. GLOBAL DATABASE
        if not os.path.exists(self.global_manifest):
            global_entities = [
                {
                    "name": "SiteConfig",
                    "primary_key": "config_key",
                    "fields": [
                        {"name": "config_key", "type": "string"},
                        {"name": "config_value", "type": "string"},
                        {"name": "description", "type": "string"}
                    ]
                },
                {
                    "name": "NavLink",
                    "fields": [
                        {"name": "label", "type": "string"},
                        {"name": "url", "type": "string"},
                        {"name": "order", "type": "integer"}
                    ]
                },
                {
                    "name": "SocialLink",
                    "fields": [
                        {"name": "platform", "type": "string"},
                        {"name": "url", "type": "string"},
                        {"name": "icon", "type": "string"}
                    ]
                },
                {
                    "name": "AuthorProfile",
                    "primary_key": "author_uuid",
                    "fields": [
                        {"name": "author_uuid", "type": "string"},
                        {"name": "name", "type": "string"},
                        {"name": "bio", "type": "string"},
                        {"name": "image_url", "type": "string"}
                    ]
                },
                {
                    "name": "AdUnit",
                    "primary_key": "ad_uuid",
                    "fields": [
                        {"name": "ad_uuid", "type": "string"},
                        {"name": "name", "type": "string"},
                        {"name": "image_url", "type": "string"},
                        {"name": "link_url", "type": "string"},
                        {"name": "zone", "type": "string"}, # sidebar, header, footer
                        {"name": "active", "type": "boolean"}
                    ]
                },
                {
                    "name": "MediaAsset",
                    "primary_key": "filename",
                    "fields": [
                        {"name": "filename", "type": "string"},
                        {"name": "original_name", "type": "string"},
                        {"name": "file_hash", "type": "string"},
                        {"name": "file_size", "type": "integer"},
                        {"name": "mime_type", "type": "string"},
                        {"name": "uploaded_at", "type": "string"}
                    ]
                }
            ]
            MFDBCore.mfdb_core_create_database(
                root_dir=self.global_db_root,
                db_name="BEJSON CMS Global",
                entities=global_entities
            )
            self.add_global_config("site_title", "boehnenelton2024")
            self.add_global_config("site_tagline", "Premium Dark Theme Templates")
            self.add_global_config("base_url", "https://boehnenelton2024.pages.dev")
            
            # Seed Social Links
            MFDBCore.mfdb_core_add_entity_record(self.global_manifest, "SocialLink", ["GitHub", "https://github.com/boehnenelton", "github"])

        # 2. CONTENT DATABASE
        if not os.path.exists(self.content_manifest):
            content_entities = [
                {
                    "name": "Category",
                    "primary_key": "slug",
                    "fields": [
                        {"name": "name", "type": "string"},
                        {"name": "slug", "type": "string"},
                        {"name": "description", "type": "string"},
                        {"name": "feed_type", "type": "string"} 
                    ]
                },
                {
                    "name": "Page",
                    "primary_key": "page_uuid",
                    "fields": [
                        {"name": "page_uuid", "type": "string"},
                        {"name": "title", "type": "string"},
                        {"name": "slug", "type": "string"},
                        {"name": "category_fk", "type": "string"},
                        {"name": "author_fk", "type": "string"},
                        {"name": "page_type", "type": "string"}, 
                        {"name": "featured_img", "type": "string"},
                        {"name": "created_at", "type": "string"}
                    ]
                },
                {
                    "name": "PageContent",
                    "fields": [
                        {"name": "page_uuid_fk", "type": "string"},
                        {"name": "html_body", "type": "string"},
                        {"name": "markdown_body", "type": "string"},
                        {"name": "source_files", "type": "array"}, 
                        {"name": "video_url", "type": "string"},
                        {"name": "pdf_url", "type": "string"},
                        {"name": "pros", "type": "array"},
                        {"name": "cons", "type": "array"},
                        {"name": "verdict_score", "type": "number"}
                    ]
                },
                {
                    "name": "StandaloneApp",
                    "primary_key": "app_uuid",
                    "fields": [
                        {"name": "app_uuid", "type": "string"},
                        {"name": "name", "type": "string"},
                        {"name": "slug", "type": "string"},
                        {"name": "description", "type": "string"},
                        {"name": "category_fk", "type": "string"},
                        {"name": "featured_img", "type": "string"},
                        {"name": "entry_file", "type": "string"},
                        {"name": "created_at", "type": "string"}
                    ]
                }
            ]
            MFDBCore.mfdb_core_create_database(
                root_dir=self.content_db_root,
                db_name="BEJSON CMS Content",
                entities=content_entities
            )
            self.add_category("Uncategorized", "uncategorized", "General posts", "blog")

    # --- Global Helpers ---
    def add_global_config(self, key: str, value: str, desc: str = ""):
        MFDBCore.mfdb_core_add_entity_record(self.global_manifest, "SiteConfig", [key, value, desc])
        self.set_dirty()

    def get_global_configs(self) -> Dict[str, str]:
        recs = MFDBCore.mfdb_core_load_entity(self.global_manifest, "SiteConfig")
        return {r["config_key"]: r["config_value"] for r in recs}

    def get_nav_links(self) -> List[Dict]:
        return MFDBCore.mfdb_core_load_entity(self.global_manifest, "NavLink")

    def add_nav_link(self, label: str, url: str, order: int = 0):
        MFDBCore.mfdb_core_add_entity_record(self.global_manifest, "NavLink", [label, url, order])
        self.set_dirty()

    def delete_nav_link(self, label: str):
        recs = self.get_nav_links()
        for i, r in enumerate(recs):
            if r["label"] == label:
                MFDBCore.mfdb_core_remove_entity_record(self.global_manifest, "NavLink", i)
                self.set_dirty()
                break

    def add_author(self, name: str, bio: str, image_url: str):
        auuid = str(uuid.uuid4())
        MFDBCore.mfdb_core_add_entity_record(self.global_manifest, "AuthorProfile", [auuid, name, bio, image_url])
        self.set_dirty()
        return auuid

    def update_author(self, author_uuid: str, name: str, bio: str, image_url: str):
        recs = self.get_authors()
        for i, r in enumerate(recs):
            if r["author_uuid"] == author_uuid:
                MFDBCore.mfdb_core_update_entity_record(self.global_manifest, "AuthorProfile", i, "name", name)
                MFDBCore.mfdb_core_update_entity_record(self.global_manifest, "AuthorProfile", i, "bio", bio)
                MFDBCore.mfdb_core_update_entity_record(self.global_manifest, "AuthorProfile", i, "image_url", image_url)
                self.set_dirty()
                break

    def delete_author(self, author_uuid: str):
        recs = self.get_authors()
        for i, r in enumerate(recs):
            if r["author_uuid"] == author_uuid:
                MFDBCore.mfdb_core_remove_entity_record(self.global_manifest, "AuthorProfile", i)
                self.set_dirty()
                break


    def get_authors(self) -> List[Dict]:
        return MFDBCore.mfdb_core_load_entity(self.global_manifest, "AuthorProfile")

    def add_ad(self, name: str, img: str, link: str, zone: str, active: bool = True):
        auuid = str(uuid.uuid4())
        MFDBCore.mfdb_core_add_entity_record(self.global_manifest, "AdUnit", [auuid, name, img, link, zone, active])
        self.set_dirty()
        return auuid

    def get_ads(self) -> List[Dict]:
        return MFDBCore.mfdb_core_load_entity(self.global_manifest, "AdUnit")

    def get_file_hash(self, file_data: bytes) -> str:
        return hashlib.sha256(file_data).hexdigest()

    def add_asset(self, filename: str, original_name: str, file_hash: str, file_size: int, mime_type: str):
        uploaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        MFDBCore.mfdb_core_add_entity_record(self.global_manifest, "MediaAsset", [filename, original_name, file_hash, file_size, mime_type, uploaded_at])
        self.set_dirty()

    def get_assets(self) -> List[Dict]:
        return MFDBCore.mfdb_core_load_entity(self.global_manifest, "MediaAsset")

    def get_asset_by_hash(self, file_hash: str) -> Optional[Dict]:
        res = MFDBCore.mfdb_core_query_entity(self.global_manifest, "MediaAsset", lambda r: r["file_hash"] == file_hash)
        return res[0] if res else None

    def delete_asset(self, filename: str):
        recs = self.get_assets()
        for i, r in enumerate(recs):
            if r["filename"] == filename:
                MFDBCore.mfdb_core_remove_entity_record(self.global_manifest, "MediaAsset", i)
                fpath = os.path.join(self.assets_dir, filename)
                if os.path.exists(fpath): os.remove(fpath)
                self.set_dirty()
                return True
        return False

    def rename_asset(self, old_filename: str, new_filename: str):
        recs = self.get_assets()
        for i, r in enumerate(recs):
            if r["filename"] == old_filename:
                MFDBCore.mfdb_core_update_entity_record(self.global_manifest, "MediaAsset", i, "filename", new_filename)
                old_path = os.path.join(self.assets_dir, old_filename)
                new_path = os.path.join(self.assets_dir, new_filename)
                if os.path.exists(old_path): os.rename(old_path, new_path)
                self.set_dirty()
                return True
        return False

    # --- Content Helpers ---
    def add_category(self, name: str, slug: str, desc: str, feed_type: str):
        MFDBCore.mfdb_core_add_entity_record(self.content_manifest, "Category", [name, slug, desc, feed_type])
        self.set_dirty()

    def update_category(self, slug: str, name: str, desc: str, feed_type: str):
        recs = MFDBCore.mfdb_core_load_entity(self.content_manifest, "Category")
        for i, r in enumerate(recs):
            if r["slug"] == slug:
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Category", i, "name", name)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Category", i, "description", desc)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Category", i, "feed_type", feed_type)
                self.set_dirty()
                break

    def delete_category(self, slug: str):
        recs = MFDBCore.mfdb_core_load_entity(self.content_manifest, "Category")
        for i, r in enumerate(recs):
            if r["slug"] == slug:
                MFDBCore.mfdb_core_remove_entity_record(self.content_manifest, "Category", i)
                self.set_dirty()
                break

    def create_page(self, title: str, category_slug: str, page_type: str, content_data: Dict[str, Any]) -> str:
        page_uuid = str(uuid.uuid4())
        page_slug = title.lower().replace(" ", "-")
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        MFDBCore.mfdb_core_add_entity_record(self.content_manifest, "Page", [page_uuid, title, page_slug, category_slug, content_data.get("author_fk", ""), page_type, content_data.get("featured_img"), created_at])
        content_values = [page_uuid, content_data.get("html_body", ""), content_data.get("markdown_body", ""), content_data.get("source_files", []), content_data.get("video_url", ""), content_data.get("pdf_url", ""), content_data.get("pros", []), content_data.get("cons", []), content_data.get("verdict_score", 0.0)]
        MFDBCore.mfdb_core_add_entity_record(self.content_manifest, "PageContent", content_values)
        self.set_dirty()
        return page_uuid

    def update_page(self, page_uuid: str, title: str, category_slug: str, page_type: str, content_data: Dict[str, Any]):
        recs = MFDBCore.mfdb_core_load_entity(self.content_manifest, "Page")
        for i, r in enumerate(recs):
            if r["page_uuid"] == page_uuid:
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Page", i, "title", title)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Page", i, "category_fk", category_slug)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Page", i, "page_type", page_type)
                if "author_fk" in content_data: MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Page", i, "author_fk", content_data["author_fk"])
                if "featured_img" in content_data: MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "Page", i, "featured_img", content_data["featured_img"])
                self.set_dirty()
                break
        crecs = MFDBCore.mfdb_core_load_entity(self.content_manifest, "PageContent")
        for i, r in enumerate(crecs):
            if r["page_uuid_fk"] == page_uuid:
                for key in ["html_body", "markdown_body", "source_files", "video_url", "pdf_url", "pros", "cons", "verdict_score"]:
                    if key in content_data: MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "PageContent", i, key, content_data[key])
                self.set_dirty()
                break

    def create_app(self, name: str, description: str, category_fk: str, featured_img: str, entry_file: str):
        app_uuid = str(uuid.uuid4())
        slug = re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        MFDBCore.mfdb_core_add_entity_record(self.content_manifest, "StandaloneApp", [app_uuid, name, slug, description, category_fk, featured_img, entry_file, created_at])
        self.set_dirty()
        return app_uuid

    def get_apps(self) -> List[Dict]:
        return MFDBCore.mfdb_core_load_entity(self.content_manifest, "StandaloneApp")

    def get_apps_in_category(self, category_slug: str) -> List[Dict]:
        return MFDBCore.mfdb_core_query_entity(self.content_manifest, "StandaloneApp", lambda r: r["category_fk"] == category_slug)

    def get_pages_in_category(self, category_slug: str) -> List[Dict]:
        return MFDBCore.mfdb_core_query_entity(self.content_manifest, "Page", lambda r: r["category_fk"] == category_slug)

    def delete_app(self, app_uuid: str):
        recs = self.get_apps()
        for i, r in enumerate(recs):
            if r["app_uuid"] == app_uuid:
                MFDBCore.mfdb_core_remove_entity_record(self.content_manifest, "StandaloneApp", i)
                app_path = os.path.join(self.apps_dir, app_uuid)
                if os.path.exists(app_path): shutil.rmtree(app_path)
                self.set_dirty()
                break

    def update_app(self, app_uuid: str, name: str, description: str, category_fk: str, featured_img: str, entry_file: str):
        recs = self.get_apps()
        for i, r in enumerate(recs):
            if r["app_uuid"] == app_uuid:
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "StandaloneApp", i, "name", name)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "StandaloneApp", i, "description", description)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "StandaloneApp", i, "category_fk", category_fk)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "StandaloneApp", i, "featured_img", featured_img)
                MFDBCore.mfdb_core_update_entity_record(self.content_manifest, "StandaloneApp", i, "entry_file", entry_file)
                self.set_dirty()
                break

    def get_full_page_data(self, page_uuid: str) -> Optional[Dict]:
        pages = MFDBCore.mfdb_core_query_entity(self.content_manifest, "Page", lambda r: r["page_uuid"] == page_uuid)
        if not pages: return None
        contents = MFDBCore.mfdb_core_query_entity(self.content_manifest, "PageContent", lambda r: r["page_uuid_fk"] == page_uuid)
        if not contents: return None
        data = {**pages[0], **contents[0]}
        if data.get("author_fk"):
            authors = MFDBCore.mfdb_core_query_entity(self.global_manifest, "AuthorProfile", lambda r: r["author_uuid"] == data["author_fk"])
            if authors: data["author"] = authors[0]
        return data
