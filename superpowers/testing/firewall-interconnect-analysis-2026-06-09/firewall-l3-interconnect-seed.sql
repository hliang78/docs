-- Generated L3 firewall connector relationships from inferred interconnects on 2026-06-09
START TRANSACTION;
DELETE FROM firewall_node_connector_connection WHERE connector_id IN ('121b0b6b-82f4-5af7-8b0a-706a1802daf3', '57a81714-4389-53c9-afa2-bdc995ebe122');
DELETE FROM firewall_connector_layout WHERE connector_id IN ('121b0b6b-82f4-5af7-8b0a-706a1802daf3', '57a81714-4389-53c9-afa2-bdc995ebe122');
DELETE FROM firewall_connector WHERE code IN ('L3AUTO55B064528B', 'L3AUTO36F2341FE7');
INSERT INTO firewall_connector (id, created_at, updated_at, deleted_at, name, code, connector_type, datacenter_id, description) VALUES
  ('121b0b6b-82f4-5af7-8b0a-706a1802daf3', NOW(3), NOW(3), NULL, 'L3 172.21.166.0/24', 'L3AUTO55B064528B', 'network_region', 'baa0f9bb-63ec-11f1-99fe-fa163e7745bf', '自动生成 L3 互联 Connector；网段=172.21.166.0/24；来源=firewall-interconnect-analysis-2026-06-09'),
  ('57a81714-4389-53c9-afa2-bdc995ebe122', NOW(3), NOW(3), NULL, 'L3 172.31.131.0/24', 'L3AUTO36F2341FE7', 'network_region', 'baa0f9bb-63ec-11f1-99fe-fa163e7745bf', '自动生成 L3 互联 Connector；网段=172.31.131.0/24；来源=firewall-interconnect-analysis-2026-06-09');
INSERT INTO firewall_node_connector_connection (id, created_at, updated_at, deleted_at, node_id, connector_id, interface_name, vrf_name, connection_type, zone_name, bandwidth, description) VALUES
  ('b2c51035-753e-5303-8d59-b1e22ef1af8e', NOW(3), NOW(3), NULL, '194762a5-63f3-11f1-99fe-fa163e7745bf', '121b0b6b-82f4-5af7-8b0a-706a1802daf3', 'M-GigabitEthernet1/0/0/0', 'management', 'direct', 'Management', NULL, '自动生成 L3 互联；network=172.21.166.0/24; evidence=shared_connected_subnet; peer=VSYS-SPLIT-MGMT'),
  ('13481e29-1cf6-5075-adae-3af561859405', NOW(3), NOW(3), NULL, 'd1221595-63ec-11f1-99fe-fa163e7745bf', '121b0b6b-82f4-5af7-8b0a-706a1802daf3', 'GigabitEthernet0/0/0', 'default', 'direct', 'UNMAPPED', NULL, '自动生成 L3 互联；network=172.21.166.0/24; evidence=shared_connected_subnet; peer=FW-172.21.166.35-H3C-M9008-BORDER'),
  ('ecb4303d-f21a-525b-8853-288dc70ceb8b', NOW(3), NOW(3), NULL, '19e81748-63f3-11f1-99fe-fa163e7745bf', '57a81714-4389-53c9-afa2-bdc995ebe122', 'meth0_0', 'VRF_MGMT', 'direct', 'UNMAPPED', NULL, '自动生成 L3 互联；network=172.31.131.0/24; evidence=shared_connected_subnet; peer=VSYS-172.31.131.5-default'),
  ('b5695576-ccc1-53be-95ea-1ca2278df359', NOW(3), NOW(3), NULL, '18a8d683-63f3-11f1-99fe-fa163e7745bf', '57a81714-4389-53c9-afa2-bdc995ebe122', 'GigabitEthernet0/0/0', 'default', 'direct', 'UNMAPPED', NULL, '自动生成 L3 互联；network=172.31.131.0/24; evidence=shared_connected_subnet; peer=FW-172.31.131.106-DP-BEIDOU-BORDER');
INSERT INTO firewall_connector_layout (id, created_at, updated_at, deleted_at, connector_id, x, y) VALUES
  ('46e3977e-325e-513a-9fc1-76746094c2c1', NOW(3), NOW(3), NULL, '121b0b6b-82f4-5af7-8b0a-706a1802daf3', 520, 260),
  ('096ff0ec-12b7-5490-855c-23b26367e80c', NOW(3), NOW(3), NULL, '57a81714-4389-53c9-afa2-bdc995ebe122', 780, 260);
COMMIT;
