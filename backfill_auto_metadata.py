import os

import mysql.connector

from backend import ensure_auto_metadata_columns, json_text_or_none
from tile_auto_metadata import analyze_tile_image


def connect():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "tile-db"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "ceramadmin"),
        password=os.environ.get("DB_PASSWORD", "glazed-dev-password"),
        database=os.environ.get("DB_NAME", os.environ.get("MYSQL_DATABASE", "tilearchive")),
        charset="utf8mb4",
    )


def main():
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    ensure_auto_metadata_columns(cursor)

    cursor.execute(
        """
        SELECT
            tp.ID,
            tp.Image,
            gt.Name AS GlazeType,
            sc.Name AS SurfaceCondition,
            tp.FiringType,
            tp.SoilType
        FROM testpiece tp
        LEFT JOIN glazetype gt ON tp.GlazeTypeID = gt.ID
        LEFT JOIN surfacecondition sc ON tp.SurfaceConditionID = sc.ID
        WHERE tp.Image IS NOT NULL
        """
    )

    rows = cursor.fetchall()
    updated = 0

    for row in rows:
        annotation = {
            "GlazeType": row.get("GlazeType") or "",
            "SurfaceCondition": row.get("SurfaceCondition") or "",
            "FiringType": row.get("FiringType") or "",
            "SoilType": row.get("SoilType") or "",
        }
        auto_metadata = analyze_tile_image(row.get("Image"), annotation)
        auto_tags = ", ".join(auto_metadata.get("tags", []))
        auto_keywords = auto_metadata.get("keywords", "")
        primary_color = auto_metadata.get("primaryColor") or None
        dominant_colors = json_text_or_none(auto_metadata.get("dominantColors"))
        color_profile = json_text_or_none(auto_metadata.get("colorProfile"))

        cursor.execute(
            """
            UPDATE testpiece
            SET AutoTags = %s,
                AutoKeywords = %s,
                PrimaryColor = %s,
                DominantColors = %s,
                ColorProfile = %s
            WHERE ID = %s
            """,
            (auto_tags, auto_keywords, primary_color, dominant_colors, color_profile, row["ID"]),
        )
        updated += 1

        if updated % 50 == 0:
            conn.commit()
            print(f"Updated {updated}/{len(rows)} tiles")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Updated {updated}/{len(rows)} tiles")


if __name__ == "__main__":
    main()
