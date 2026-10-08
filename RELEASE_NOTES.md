# Release Notes

## 20261009

- 优化了revo3外观

## v2026.10.05

### Appearance

- Make the approved 2026-09-20 Revotron metallic-paint appearance the default for single-arm and bimanual Revo3 assemblies, including MX Touch variants, using the existing URDF filenames.
- Add silver shells, dark gray trim, cyan light covers, logos, a static face expression, rear-head rainbow details, column markings, and control-panel details.
- Replace the original base, chest, and head visual meshes with 62 split and decorative meshes. Preserve Revotron joint, inertial, and collision definitions.
- Refresh Revotron URDF previews and add appearance detail views and a MuJoCo preview.

### Model exports

- Regenerate the public URDF, MJCF, and USD assets from the upstream description packages, with appearance definitions maintained in the source packages for future generation.
- Preserve global and inline URDF colors in MJCF, retain tactile marker primitives, and use shell inertia for decorative surface meshes so they load in MuJoCo.
- Regenerate USD with v4 settings: fixed bases, merged fixed joints, zero drive stiffness/damping, disabled gravity, self-collision, and 16/4 position/velocity solver iterations. Retain the Revo3 palm decomposition and 32 thumb collision hulls per hand.
- Preserve USD visual material colors and export flattened, non-instanced assets without unresolved importer references.
- Store the two bimanual Revotron USD files with Git LFS; run `git lfs pull` after cloning to retrieve the model data.

### Validation

- Validate all 21 public model sets: load MJCF in MuJoCo, reopen USD, compare visual geometry and colors with URDF, and check the USD physics settings. These checks cover loading and exported properties; they do not add new dynamics or collision-accuracy validation.

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
