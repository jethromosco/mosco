"""
Centralized Photo Operations

Handles all photo-related operations (saving, loading, deletion, compression)
using AppContext as the single source of truth for photo folder paths.

This eliminates duplication and ensures photos are always saved to the correct folder
regardless of how many times categories are switched.
"""

import os
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from app_context import get_app_context
from debug import DEBUG_MODE


def sanitize_dimension_for_filename(value: Any) -> str:
    """
    Sanitize dimension value for use in filename.
    
    Converts fractions (with /) and decimals to safe filename format.
    CRITICAL: Must match category admin modules for consistency.
    
    Examples:
        5/8 -> 5x8 (fractions converted to x)
        5.5-6.5 -> 5.5-6.5 (ranges with dash preserved)
        5.5/6.5 -> 5.5x6.5 (slash range to x)
    """
    try:
        val_str = str(value)
        # CRITICAL FIX: Replace slashes with 'x' (not underscore) for compatibility
        # This matches the sanitization in category admin modules
        val_str = val_str.replace("/", "x")
        # Remove spaces
        val_str = val_str.replace(" ", "")
        return val_str
    except Exception:
        return str(value).replace("/", "x").replace(" ", "")


def create_safe_filename(details: Dict[str, Any], extension: str) -> str:
    """
    Create safe filename for photo storage.
    
    Ensures dimensions and brand are sanitized for filesystem compatibility.
    
    Args:
        details: Product details dict with keys: type, id, od, th, brand
        extension: File extension (e.g., '.jpg')
    
    Returns:
        Safe filename string
    """
    safe_id = sanitize_dimension_for_filename(details.get('id', ''))
    safe_od = sanitize_dimension_for_filename(details.get('od', ''))
    safe_th = sanitize_dimension_for_filename(details.get('th', ''))
    safe_brand = str(details.get('brand', '')).replace('/', 'x').replace(' ', '_')
    
    product_type = str(details.get('type', '')).replace(' ', '')
    return f"{product_type}-{safe_id}-{safe_od}-{safe_th}-{safe_brand}{extension}"


def get_photo_folder() -> str:
    """
    Get photo folder from AppContext.
    
    CRITICAL: Always reads from AppContext to ensure consistency
    when categories are switched.
    CRITICAL: Normalizes path separators (fixes Windows mixed / and \\ issues)
    
    Returns:
        Full path to photo folder (normalized)
    """
    context = get_app_context()
    folder = context.photo_folder
    
    # CRITICAL FIX: Normalize path separators to prevent Windows path joining issues
    if folder:
        folder = os.path.normpath(folder)
    
    if DEBUG_MODE:
        print(f"[DEBUG-PHOTO] get_photo_folder() -> {folder}")
    
    return folder


def save_photo(
    source_path: str,
    details: Dict[str, Any],
    max_size_mb: int = 5
) -> Tuple[bool, str]:
    """
    Save and compress photo for a product.
    
    Uses AppContext.photo_folder as destination.
    
    Args:
        source_path: Path to source image file
        details: Product details (type, id, od, th, brand)
        max_size_mb: Maximum file size in MB
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        context = get_app_context()
        # DEBUG: Log save operation with current AppContext
        print(f"[DEBUG-SAVE] Saving photo | Category: {context.active_category} | Folder: {context.photo_folder}")
        
        if DEBUG_MODE:
            print(f"[DEBUG-PHOTO] Saving photo from {source_path}")
            print(f"[DEBUG-PHOTO] Details: {details}")
        
        photo_folder = context.photo_folder
        
        if not photo_folder:
            return False, "Photo folder not configured in AppContext"
        
        if not os.path.exists(photo_folder):
            try:
                os.makedirs(photo_folder, exist_ok=True)
            except Exception as e:
                return False, f"Failed to create photo folder: {e}"
        
        # Only MOS brand uploads are allowed
        if str(details.get('brand', '')).upper() != 'MOS':
            return False, "Only MOS brand products can have custom photos"
        
        # Create safe filename
        _, ext = os.path.splitext(source_path)
        if ext.lower() not in ['.jpg', '.jpeg', '.png']:
            ext = '.jpg'
        
        safe_filename = create_safe_filename(details, ext)
        # CRITICAL FIX: Normalize path separators before joining
        photo_folder = os.path.normpath(photo_folder)
        target_path = os.path.join(photo_folder, safe_filename)
        
        if DEBUG_MODE:
            print(f"[DEBUG-PHOTO] Saving to: {target_path}")
            print(f"[DEBUG-PHOTO] Context.photo_folder: {context.photo_folder}")
            print(f"[DEBUG-PHOTO] Normalized folder: {photo_folder}")
        
        # Compress and save
        if compress_and_save_image(source_path, target_path, max_size_mb):
            if DEBUG_MODE:
                print(f"[DEBUG-PHOTO] Photo saved successfully: {target_path}")
            return True, f"Photo saved: {safe_filename}"
        else:
            return False, "Failed to compress/save photo"
    
    except Exception as e:
        err_msg = f"Error saving photo: {e}"
        print(f"[ERROR-PHOTO] {err_msg}")
        return False, err_msg


def compress_and_save_image(
    source_path: str,
    target_path: str,
    max_size_mb: int = 5
) -> bool:
    """
    Compress and save image with size limit.
    
    CRITICAL: Normalizes path separators on Windows to prevent path issues.
    
    Args:
        source_path: Source image path
        target_path: Target image path
        max_size_mb: Maximum size in MB
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # CRITICAL FIX: Normalize path separators
        target_path = os.path.normpath(target_path)
        
        img = Image.open(source_path).convert("RGB")
        quality = 95
        max_size_bytes = max_size_mb * 1024 * 1024
        
        while True:
            img.save(target_path, format="JPEG", quality=quality)
            if os.path.getsize(target_path) <= max_size_bytes or quality <= 60:
                break
            quality -= 5
        
        if DEBUG_MODE:
            print(f"[DEBUG-PHOTO] Compressed image saved with quality={quality}")
        return True
    except Exception as e:
        print(f"[ERROR-PHOTO] Compression failed: {e}")
        return False


def get_photo_path(details: Dict[str, Any]) -> Optional[str]:
    """
    Get path to photo file for a product.
    
    Handles both MOS custom uploads and predefined brand images.
    Implements case-insensitive filename matching and multiple extension variants.
    
    Args:
        details: Product details (type, id, od, th, brand)
    
    Returns:
        Full path to photo, or None if not found
    """
    try:
        photo_folder = get_photo_folder()
        if not photo_folder:
            if DEBUG_MODE:
                print(f"[DEBUG-PHOTO] Photo folder not available")
            return None
        
        # CRITICAL FIX: Ensure path is normalized
        photo_folder = os.path.normpath(photo_folder)
        
        brand = str(details.get('brand', '')).upper()
        
        # MOS brand: custom uploaded images
        if brand == 'MOS':
            safe_id = sanitize_dimension_for_filename(details.get('id', ''))
            safe_od = sanitize_dimension_for_filename(details.get('od', ''))
            safe_th = sanitize_dimension_for_filename(details.get('th', ''))
            safe_brand = details.get('brand', '').replace('/', 'x').replace(' ', '_')
            
            base = f"{details.get('type', '')}-{safe_id}-{safe_od}-{safe_th}-{safe_brand}"
            
            # CRITICAL FIX: Try multiple extensions (case variants) for better compatibility
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                candidate = os.path.join(photo_folder, base + ext)
                if DEBUG_MODE:
                    print(f"[DEBUG-PHOTO] Checking MOS: {candidate}")
                if os.path.exists(candidate):
                    if DEBUG_MODE:
                        print(f"[DEBUG-PHOTO] MOS photo found: {candidate}")
                    return candidate
            
            # CRITICAL FIX: Case-insensitive and underscore/x-insensitive fallback scan
            # Handles old files that were saved with '_' instead of 'x' in dimensions
            try:
                if os.path.exists(photo_folder):
                    # Normalize base for comparison (try both x and _)
                    base_normalized = base.replace("x", "_").lower()
                    
                    for f in os.listdir(photo_folder):
                        name, ext = os.path.splitext(f)
                        # Normalize filename to allow x/_ interchangeability
                        name_normalized = name.replace("x", "_").lower()
                        
                        if name_normalized == base_normalized and ext.lower() in ['.jpg', '.jpeg', '.png']:
                            candidate = os.path.join(photo_folder, f)
                            if DEBUG_MODE:
                                print(f"[DEBUG-PHOTO] MOS photo found (flexible match): {candidate}")
                            return candidate
            except Exception as scan_err:
                if DEBUG_MODE:
                    print(f"[DEBUG-PHOTO] Flexible scan failed: {scan_err}")
            
            if DEBUG_MODE:
                print(f"[DEBUG-PHOTO] MOS photo not found for {base} in {photo_folder}")
            return None
        
        # Non-MOS brand: predefined images (db.jpg, tc.jpg, nqk.jpg, nok.jpg, dh.jpg, etc.)
        product_type = str(details.get('type', '')).lower()
        
        # CRITICAL FIX: Try multiple extensions for predefined photos
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            candidate = os.path.join(photo_folder, product_type + ext)
            if DEBUG_MODE:
                print(f"[DEBUG-PHOTO] Checking predefined: {candidate}")
            if os.path.exists(candidate):
                if DEBUG_MODE:
                    print(f"[DEBUG-PHOTO] Predefined photo found: {candidate}")
                return candidate
        
        # CRITICAL FIX: Case-insensitive fallback for predefined photos
        try:
            if os.path.exists(photo_folder):
                for f in os.listdir(photo_folder):
                    name, ext = os.path.splitext(f)
                    if name.lower() == product_type and ext.lower() in ['.jpg', '.jpeg', '.png']:
                        candidate = os.path.join(photo_folder, f)
                        if DEBUG_MODE:
                            print(f"[DEBUG-PHOTO] Predefined photo found (case-insensitive): {candidate}")
                        return candidate
        except Exception as scan_err:
            if DEBUG_MODE:
                print(f"[DEBUG-PHOTO] Case-insensitive scan failed: {scan_err}")
        
        if DEBUG_MODE:
            print(f"[DEBUG-PHOTO] Predefined photo not found for type: {product_type} in {photo_folder}")
        return None
    
    except Exception as e:
        print(f"[ERROR-PHOTO] Error getting photo path: {e}")
        return None


def delete_old_images(details: Dict[str, Any]) -> None:
    """
    Delete old image files for a product.
    
    CRITICAL: For MOS brand, deletes old uploads.
    For non-MOS brand, only deletes if switching FROM MOS.
    Never modifies predefined brand images.
    
    Args:
        details: Product details (type, id, od, th, brand)
    """
    try:
        photo_folder = get_photo_folder()
        if not photo_folder:
            return
        
        brand = str(details.get('brand', '')).upper()
        
        # Only delete for MOS brand (custom uploads)
        if brand == 'MOS':
            safe_id = sanitize_dimension_for_filename(details.get('id', ''))
            safe_od = sanitize_dimension_for_filename(details.get('od', ''))
            safe_th = sanitize_dimension_for_filename(details.get('th', ''))
            safe_brand = details.get('brand', '').replace('/', 'x').replace(' ', '_')
            
            mos_base = f"{details.get('type', '')}-{safe_id}-{safe_od}-{safe_th}-{safe_brand}"
            
            for ext in ['.jpg', '.jpeg', '.png']:
                old_path = os.path.join(photo_folder, mos_base + ext)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        if DEBUG_MODE:
                            print(f"[DEBUG-PHOTO] Deleted old image: {old_path}")
                    except Exception as e:
                        print(f"[ERROR-PHOTO] Failed to delete {old_path}: {e}")
        
        # Never delete predefined images for non-MOS brands
    
    except Exception as e:
        print(f"[ERROR-PHOTO] Error deleting old images: {e}")


def calculate_image_display_size(image_path: str, max_width: int, max_height: int) -> Tuple[int, int]:
    """
    Calculate display size for image.
    
    Scales to fill box while maintaining aspect ratio.
    """
    try:
        img = Image.open(image_path)
        orig_width, orig_height = img.size
        
        width_ratio = max_width / orig_width if orig_width > 0 else 1
        height_ratio = max_height / orig_height if orig_height > 0 else 1
        scale_factor = max(width_ratio, height_ratio)
        
        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)
        return new_width, new_height
    except Exception:
        return max_width, max_height


def validate_image_file(file_path: str) -> bool:
    """
    Validate if file is a supported image format.
    
    Args:
        file_path: Path to image file
    
    Returns:
        True if valid, False otherwise
    """
    if not file_path:
        return False
    
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ['.jpg', '.jpeg', '.png']


def rename_photo_if_needed(
    old_details: Dict[str, Any],
    new_details: Dict[str, Any]
) -> bool:
    """
    Rename photo file when product dimensions change.
    
    Only renames MOS uploads when dimensions actually change.
    
    Args:
        old_details: Original product details
        new_details: Updated product details
    
    Returns:
        True if rename successful or not needed, False if error
    """
    try:
        # Only rename for MOS brand
        if str(new_details.get('brand', '')).upper() != 'MOS':
            return True
        if str(old_details.get('brand', '')).upper() != 'MOS':
            return True
        
        # Check if dimensions actually changed
        dims_changed = (
            old_details.get('type') != new_details.get('type') or
            old_details.get('id') != new_details.get('id') or
            old_details.get('od') != new_details.get('od') or
            old_details.get('th') != new_details.get('th')
        )
        
        if not dims_changed:
            return True
        
        photo_folder = get_photo_folder()
        if not photo_folder:
            return True
        
        # Build old filename
        safe_id = sanitize_dimension_for_filename(old_details.get('id', ''))
        safe_od = sanitize_dimension_for_filename(old_details.get('od', ''))
        safe_th = sanitize_dimension_for_filename(old_details.get('th', ''))
        safe_brand = old_details.get('brand', '').replace('/', 'x').replace(' ', '_')
        old_base = f"{old_details.get('type', '')}-{safe_id}-{safe_od}-{safe_th}-{safe_brand}"
        
        # Find old file
        old_path = None
        for ext in ['.jpg', '.jpeg', '.png']:
            candidate = os.path.join(photo_folder, old_base + ext)
            if os.path.exists(candidate):
                old_path = candidate
                break
        
        if not old_path:
            return True  # No old file to rename
        
        # Create new filename
        _, ext = os.path.splitext(old_path)
        new_filename = create_safe_filename(new_details, ext)
        new_path = os.path.join(photo_folder, new_filename)
        
        # Rename file
        try:
            os.replace(old_path, new_path)
            if DEBUG_MODE:
                print(f"[DEBUG-PHOTO] Renamed photo from {old_base} to {new_filename}")
            return True
        except Exception as e:
            # Try copy+delete as fallback
            try:
                import shutil
                shutil.copy2(old_path, new_path)
                os.remove(old_path)
                if DEBUG_MODE:
                    print(f"[DEBUG-PHOTO] Copied then deleted photo (rename fallback)")
                return True
            except Exception:
                print(f"[ERROR-PHOTO] Failed to rename photo: {e}")
                return False
    
    except Exception as e:
        print(f"[ERROR-PHOTO] Error in rename_photo_if_needed: {e}")
        return False
