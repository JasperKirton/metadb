import json
import uuid

from sqlalchemy.sql import text

from . import db
from . import exceptions


def add_token(admin=False):
    """ Add a new token to the database and return it
        Arguments:
          admin: True if this token has admin privileges
    """
    query = text("""
        INSERT INTO token (token, admin)
             VALUES (:token, :admin)""")
    with db.engine.begin() as connection:
        token = str(uuid.uuid4())
        result = connection.execute(query, {"token": token, "admin": admin})
        return token


def remove_token(token):
    try:
        uuid.UUID(token, version=4)
    except ValueError:
        return
    query = text("""
        DELETE FROM token
              WHERE token = :token""")
    with db.engine.begin() as connection:
        connection.execute(query, {"token": token})


def get_tokens():
    query = text("""
        SELECT token::text
             , admin
          FROM token
      ORDER BY added""")
    with db.engine.begin() as connection:
        rows = connection.execute(query)
        return [dict(r) for r in rows.fetchall()]


def get_token(token):
    try:
        uuid.UUID(token, version=4)
    except ValueError:
        return {}
    query = text("""
        SELECT token::text
             , admin
          FROM token
         WHERE token = :token""")
    with db.engine.begin() as connection:
        result = connection.execute(query, {"token": token})
        if result.rowcount:
            return dict(result.fetchone())
        else:
            return {}


def add_source(name):
    query = text("""
        INSERT INTO source (name)
             VALUES (:name)
          RETURNING id""")
    with db.engine.begin() as connection:
        result = connection.execute(query, {"name": name})
        id = result.fetchone()[0]
        return {"name": name, "id": id}


def add_recording_mbids(mbids):
    """ Add some recording musicbrainzids to the recording table.
        Returns mbids which were added.
    """
    check_query = text("""
        SELECT mbid
          FROM recording
         WHERE mbid = :mbid""")
    insert_query = text("""
        INSERT INTO recording (mbid)
             VALUES (:mbid)""")
    ret = []
    with db.engine.begin() as connection:
        for mbid in mbids:
            result = connection.execute(check_query, {"mbid": mbid})
            if not result.rowcount:
                connection.execute(insert_query, {"mbid": mbid})
                ret.append(mbid)
    return ret


def get_recording_mbids():
    query = text("""
        SELECT mbid::text
          FROM recording
      ORDER BY added""")
    with db.engine.begin() as connection:
        result = connection.execute(query)
        return [dict(r) for r in result.fetchall()]


def load_source(name):
    query = text("""
        SELECT id
             , name
          FROM source
         WHERE name = :name""")
    with db.engine.begin() as connection:
        result = connection.execute(query, {"name": name})
        row = result.fetchone()
        if row:
            return {"id": row.id, "name": row.name}
    return None


def add_scraper(source, module, version, description):
    query = text("""
        INSERT INTO scraper (source_id, module, version, description)
             VALUES (:source_id, :module, :version, :description)
          RETURNING id
        """)
    with db.engine.begin() as connection:
        result = connection.execute(query, {"source_id": source["id"],
                                            "module": module,
                                            "version": version,
                                            "description": description})
        row = result.fetchone()
        return {"id": row.id, "module": module,
                "version": version, "description": description}


def load_scrapers_for_source(source):
    query = text("""
        SELECT id
             , source_id
             , module
             , version
          FROM scraper
         WHERE source_id = :source_id
        """)
    with db.engine.begin() as connection:
        result = connection.execute(query, {"source_id": source["id"]})
        rows = result.fetchall()
        ret = []
        for r in rows:
            ret.append({"id": r.id,
                        "source_id": r.source_id,
                        "version": r.version,
                        "module": r.module})
        return ret


def load_latest_scraper_for_source(source):
    query = text("""
        SELECT id
             , source_id
             , version
             , scraper
          FROM scraper
         WHERE source_id = :source_id
      ORDER BY version DESC
         LIMIT 1
        """)
    with db.engine.begin() as connection:
        result = connection.execute(query, {"source_id": source["id"]})
        row = result.fetchone()
        if row:
            return {"id": row.id,
                    "source_id": row.source_id,
                    "version": row.version,
                    "scraper": row.scraper}
    return None


def add_item(scraper, mbid, data):
    with db.engine.begin() as connection:
        return _add_item_w_connection(connection, scraper, mbid, data)


def _add_item_w_connection(connection, scraper, mbid, data):
    item_query = text("""
        INSERT INTO item (scraper_id, mbid)
             VALUES (:scraper_id, :mbid)
          RETURNING id
        """)

    item_data_query = text("""
        INSERT INTO item_data (item_id, data)
             VALUES (:item_id, :data)
        """)

    result = connection.execute(item_query, {"scraper_id": scraper["id"],
                                             "mbid": mbid})
    row = result.fetchone()
    id = row.id
    if isinstance(data, dict):
        data = json.dumps(data)
    connection.execute(item_data_query, {"item_id": id,
                                         "data": data})

    return {"id": id, "mbid": mbid, "scraper_id": scraper["id"],
            "data": data}


def load_item(mbid, source_name):
    source = load_source(source_name)
    scraper = load_latest_scraper_for_source(source)
    query = text("""
        SELECT item.id,
               item.mbid,
               item.added,
               item_data.data
          FROM item
     LEFT JOIN item_data
            ON item_data.item_id = item.id
         WHERE item.mbid = :mbid
           AND item.scraper_id = :scraper_id
        """)
    with db.engine.begin() as connection:
        result = connection.execute(query, {"scraper_id": scraper["id"],
                                            "mbid": mbid})
        row = result.fetchone()
        if row:
            return {"id": row.id, "mbid": row.mbid, "added": row.added,
                    "data": row.data}

    return None


