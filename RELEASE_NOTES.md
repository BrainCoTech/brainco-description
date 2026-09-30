# Release Notes

## v2026.09.30

- Update both Revo3 hands with 32 trimmed thumb CMR collision meshes per hand and backtrimmed palm collision meshes.
- Propagate the collision geometry to Revo3, RevoArm, and Revotron URDF, MJCF, and USD models.

### Appearance

- Revotron: Revotron-basic new ID.
- Revo3: Revo3 MX Touch / basic silver version.
- Revomate/arm: ID not yet updated.
- Revo2: Product version.

### Kinematics

- Revotron: Validated.
- Revo3: Validated.
- Revomate/arm: Validated.
- Revo2: Validated.

### Dynamics

- Revotron: Validated.
- Revo3: Validated.
- Revomate/arm: Not yet validated.
- Revo2: Validated.

### Collision

- Revotron: Not yet processed.
- Revo3: Self-collision fixes added; validation pending.
- Revomate/arm: Not yet processed.
- Revo2: Not yet processed.

## v2026.09.29

- Add Revotron camera coordinate frames and wrist cameras.
- Add head OAK and left/right wrist camera meshes, with updated mounting transforms and inertial properties.
- Update Revotron wrist connectors and the corresponding URDF, MJCF, and USD models.

## v2026.09.26

- Add Revo3 MX touch and without-touch model variants.
- Fix Revo3 inertia parameters using legacy mass properties transformed into the updated link frames.
- Fix Revo3 MPR joint definitions.
- Add Revo3 appearance materials and updated previews.
- Revo3 collision meshes are not yet processed in this version.
- Add the RevoTron ID appearance.
