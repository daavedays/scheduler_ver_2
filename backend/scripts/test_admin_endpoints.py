import json
from typing import Any, Dict, List


def run_tests() -> None:
    # Import app and config
    try:
        from backend.app import app
    except Exception:
        from app import app  # type: ignore

    results: List[str] = []

    with app.test_client() as client:
        # Helper: login
        def login() -> None:
            resp = client.post('/api/login', json={'username': 'Dav', 'password': '8320845'})
            assert resp.status_code == 200, f"login failed: {resp.status_code} {resp.data!r}"
            data = resp.get_json() or {}
            assert data.get('success'), f"login response unexpected: {data}"

        # Ensure auth required for protected routes
        r = client.get('/api/y-tasks/definitions')
        assert r.status_code == 401, f"expected 401 before login, got {r.status_code}"
        r = client.get('/api/x-tasks/definitions')
        assert r.status_code == 401, f"expected 401 before login, got {r.status_code}"
        results.append('Auth gates OK')

        # Login
        login()

        # Snapshot originals for restore at the end
        y_defs_resp = client.get('/api/y-tasks/definitions')
        assert y_defs_resp.status_code == 200, y_defs_resp.data
        y_defs_orig: List[Dict[str, Any]] = (y_defs_resp.get_json() or {}).get('definitions') or []

        x_defs_resp = client.get('/api/x-tasks/definitions')
        assert x_defs_resp.status_code == 200, x_defs_resp.data
        x_defs_orig: List[Dict[str, Any]] = (x_defs_resp.get_json() or {}).get('definitions') or []

        try:
            # --- Y definitions CRUD ---
            # Create
            new_y = {
                'name': 'TestY__DO_NOT_KEEP',
                'requiresQualification': False,
                'autoAssign': True,
            }
            r = client.post('/api/y-tasks/definitions', json=new_y)
            assert r.status_code == 200, r.data
            created = (r.get_json() or {}).get('definition') or {}
            assert created.get('name') == new_y['name'], created
            y_id = created.get('id')
            assert isinstance(y_id, int), created

            # Read
            r = client.get('/api/y-tasks/definitions')
            assert r.status_code == 200
            names = [d.get('name') for d in (r.get_json() or {}).get('definitions') or []]
            assert new_y['name'] in names

            # Update
            r = client.patch(f'/api/y-tasks/definitions/{y_id}', json={'requiresQualification': True, 'autoAssign': False})
            assert r.status_code == 200, r.data
            updated = (r.get_json() or {}).get('definition') or {}
            assert updated.get('requiresQualification') is True
            assert updated.get('autoAssign') is False

            # Edge: update nonexistent
            r = client.patch('/api/y-tasks/definitions/9999999', json={'autoAssign': False})
            assert r.status_code == 404

            # Edge: add invalid (missing name)
            r = client.post('/api/y-tasks/definitions', json={'requiresQualification': True})
            assert r.status_code == 400

            # Delete
            r = client.delete(f'/api/y-tasks/definitions/{y_id}')
            assert r.status_code == 200
            # Edge: delete again
            r = client.delete(f'/api/y-tasks/definitions/{y_id}')
            assert r.status_code == 404
            results.append('Y CRUD OK')

            # --- X definitions CRUD ---
            # Create
            new_x = {
                'name': 'TestX__DO_NOT_KEEP',
                'start_day': 0,
                'end_day': 3,
                'duration_days': 4,
                'isDefault': False,
            }
            r = client.post('/api/x-tasks/definitions', json=new_x)
            assert r.status_code == 200, r.data
            created = (r.get_json() or {}).get('definition') or {}
            assert created.get('name') == new_x['name'], created
            x_id = created.get('id')
            assert isinstance(x_id, int)

            # Read
            r = client.get('/api/x-tasks/definitions')
            assert r.status_code == 200
            names = [d.get('name') for d in (r.get_json() or {}).get('definitions') or []]
            assert new_x['name'] in names

            # Update (change days and remove duration)
            r = client.patch(f'/api/x-tasks/definitions/{x_id}', json={'start_day': 6, 'end_day': 5, 'duration_days': None})
            assert r.status_code == 200, r.data
            updated = (r.get_json() or {}).get('definition') or {}
            assert updated.get('start_day') == 6 and updated.get('end_day') == 5

            # Edge: invalid POST (missing numeric days)
            r = client.post('/api/x-tasks/definitions', json={'name': 'BadX'})
            assert r.status_code == 400

            # Delete
            r = client.delete(f'/api/x-tasks/definitions/{x_id}')
            assert r.status_code == 200
            # Edge: delete again
            r = client.delete(f'/api/x-tasks/definitions/{x_id}')
            assert r.status_code == 404
            results.append('X CRUD OK')

            # --- Backward compatible names-only endpoint for Y ---
            # Keep existing names and add one temporary name
            r = client.get('/api/y-tasks/definitions')
            cur_defs = (r.get_json() or {}).get('definitions') or []
            names = [d.get('name') for d in cur_defs]
            added_name = 'TempY__DO_NOT_KEEP'
            names_with_added = names + [added_name]
            r = client.post('/api/y-tasks/types', json={'types': names_with_added})
            assert r.status_code == 200, r.data
            out = r.get_json() or {}
            out_names = out.get('types') or [d.get('name') for d in out.get('definitions') or []]
            assert added_name in out_names
            results.append('Y types (names-only) endpoint OK')

        finally:
            # Restore originals
            rr = client.put('/api/y-tasks/definitions', json={'definitions': y_defs_orig})
            assert rr.status_code == 200, rr.data
            rr = client.put('/api/x-tasks/definitions', json={'definitions': x_defs_orig})
            assert rr.status_code == 200, rr.data

    print(json.dumps({
        'ok': True,
        'results': results
    }, indent=2))


if __name__ == '__main__':
    run_tests()


