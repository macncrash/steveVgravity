# --- Gravity knobs (copy these from the Gravity sim; lengths there are metres, here mm) ---
pods = 12  # Number of pods (dandelion seeds)
k = 6  # Repulsion hardness: 1 = Thomson (electrons), 12 = near Tammes (hard spheres)
start = 0  # Start layout: 0 = Fibonacci, 1 = seeded random
seed = 7  # Random seed (used when start = 1)
relax = 1  # 1 = run the 1200-iteration repulsion, 0 = pure Fibonacci
hub_r = 3000  # mm Hub sphere radius (Gravity 'hub' x 1000)
reach = 6000  # mm Stalk / tunnel length (Gravity 'reach' x 1000)
pod_r = 2030  # mm Pod radius, Spacelab 4.06 m diameter (Gravity 'podR' x 1000)
segments = 7  # Spacelab segments per pod (Gravity 'segments')
bloom_d = 12000  # mm Solar bloom diameter (Gravity 'bloomD' x 1000)
order = 0  # Assembly order: 0 = opposite pairs (decussate), 1 = biggest gap (phyllotaxis inhibitor), 2 = index
launches = 6  # Launches flown: 1 = hub + docking pod, then one pod per launch (Gravity 'launch')
berthing = 1  # 1 = the last launch's pod arrives as 7 flight segments in the New Shuttle's bay (animation 'berthing')
shuttle_stretch = 8000  # mm New Shuttle bay stretch (26.3 m bay: ODS + 7 flight segments, clear of the OMS pods); 0 = original
# --- CAD-only detail ---
seg_len = 2900  # mm One flight segment: 2.7 m Spacelab shell + two 100 mm berthing flanges
cone_len = 1300  # mm Spacelab end cone length
cone_r = 1300  # mm End cone small radius
mast = 7500  # mm Gimbal mast from cone tip to bloom centre (> bloom radius so a bloom never cuts its own pod)
rad_w = 3000  # mm Radiator fin width
tunnel_r = 600  # mm Pressurized tunnel radius
