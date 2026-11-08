"""Verify disposable-container guards without any engine or database access."""
import copy
import json
import os
import unittest
from unittest.mock import patch

from setup_adonet_membership import verified_target


class MembershipTargetTests(unittest.TestCase):
    def setUp(self):
        self.container = {
            "Id": "a" * 64,
            "Config": {"Labels": {"org.jmfloreszazo.experiment": "e2-cluster"},
                       "Env": ["POSTGRES_DB=e2lab"]},
            "State": {"Running": True},
            "NetworkSettings": {"Ports": {"5432/tcp": [
                {"HostIp": "127.0.0.1", "HostPort": "55001"}
            ]}},
        }

    def resolve(self, container, engine="docker"):
        with patch("setup_adonet_membership.subprocess.check_output",
                   return_value=json.dumps([container]).encode()) as inspect:
            result = verified_target(engine, "book-lab-123456-789")
        inspect.assert_called_once_with([engine, "inspect", "book-lab-123456-789"], timeout=15)
        return result

    def test_owned_loopback_database_resolves_to_immutable_id(self):
        for engine in ("docker", "podman"):
            with self.subTest(engine=engine):
                self.assertEqual(self.resolve(self.container, engine), "a" * 64)

    def test_wrong_label_database_or_state_is_rejected(self):
        for key in ("label", "database", "state"):
            container = copy.deepcopy(self.container)
            if key == "label":
                container["Config"]["Labels"] = {}
            elif key == "database":
                container["Config"]["Env"] = ["POSTGRES_DB=production"]
            else:
                container["State"]["Running"] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.resolve(container)

    def test_public_or_missing_port_binding_is_rejected(self):
        for bindings in ([], [{"HostIp": "0.0.0.0", "HostPort": "5432"}]):
            container = copy.deepcopy(self.container)
            container["NetworkSettings"]["Ports"]["5432/tcp"] = bindings
            with self.subTest(bindings=bindings), self.assertRaises(ValueError):
                self.resolve(container)

    def test_invalid_engine_and_unowned_names_are_rejected_before_inspection(self):
        with patch("setup_adonet_membership.subprocess.check_output") as inspect:
            for engine, name in (("other", "e2-postgres"), ("docker", "production"),
                                 ("docker", "book-lab-1-2-extra")):
                with self.subTest(engine=engine, name=name), self.assertRaises(ValueError):
                    verified_target(engine, name)
            inspect.assert_not_called()

    def test_existing_named_fixture_is_preserved(self):
        self.assertEqual(verified_target("podman", "e2-postgres"), "e2-postgres")

    def test_network_fixture_still_requires_explicit_opt_in(self):
        with patch.dict(os.environ, {"E2_NETWORK_TEST": ""}):
            with self.assertRaises(ValueError):
                verified_target("podman", "e2f10-pg")
        with patch.dict(os.environ, {"E2_NETWORK_TEST": "1"}):
            self.assertEqual(verified_target("podman", "e2f10-pg"), "e2f10-pg")

    def test_short_container_id_is_rejected(self):
        self.container["Id"] = "a" * 12
        with self.assertRaises(ValueError):
            self.resolve(self.container)


if __name__ == "__main__":
    unittest.main()
