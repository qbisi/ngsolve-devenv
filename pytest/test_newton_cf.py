#!/usr/bin/env python
# coding: utf-8

import numpy as np
from ngsolve import *
from ngsolve.comp import IntegrationRuleSpace
from ngsolve.fem import MinimizationCF, NewtonCF
from netgen.csg import *
import netgen

import pytest


def mk_fes_ir():
    # 'minimal' mesh
    m = netgen.meshing.Mesh(dim=1)

    N = 1
    pnums = []
    for i in range(0, N + 1):
        pnums.append(m.Add(netgen.meshing.MeshPoint(Pnt(2 * i / N, 0, 0))))

    idx = m.AddRegion("material", dim=1)
    for i in range(0, N):
        m.Add(netgen.meshing.Element1D([pnums[i], pnums[i + 1]], index=idx))

    idx_left = m.AddRegion("left", dim=0)
    idx_right = m.AddRegion("right", dim=0)

    m.Add(netgen.meshing.Element0D(pnums[0], index=idx_left))
    m.Add(netgen.meshing.Element0D(pnums[N], index=idx_right))

    mesh = Mesh(m)

    int_order = 0

    fes_ir = IntegrationRuleSpace(mesh, order=int_order)
    return fes_ir


@pytest.fixture
def fes_ir():
    return mk_fes_ir()


def test_scalar_linear_minimization(fes_ir):
    u = GridFunction(fes_ir)
    du = fes_ir.TrialFunction()

    pot = du ** 2 - du / 2
    eq = 2 * du - 1 / 2

    expected = np.array([1 / 4])

    u.Interpolate(CoefficientFunction(3))
    ncf = NewtonCF(eq.Compile(realcompile=True, wait=True, maxderiv=1), u, maxiter=2)
    u.Interpolate(ncf)
    assert np.allclose(u.vec.FV().NumPy(), expected, atol=1e-14, rtol=0)

    u.Interpolate(CoefficientFunction(3))
    mcf = MinimizationCF(pot.Compile(realcompile=True, wait=True, maxderiv=2), u, maxiter=2)
    u.Interpolate(mcf)
    assert np.allclose(u.vec.FV().NumPy(), expected, atol=1e-14, rtol=0)


def test_scalar_nonlinear_minimization(fes_ir):
    u = GridFunction(fes_ir)
    du = fes_ir.TrialFunction()

    pot = du ** 3 - du ** 2 / 2
    eq = 3 * du ** 2 - du

    expected = np.array([1 / 3])

    u.Interpolate(CoefficientFunction(3))
    ncf = NewtonCF(eq, u, tol=1e-8)
    u.Interpolate(ncf)
    assert np.allclose(u.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    u.Interpolate(CoefficientFunction(3))
    mcf = MinimizationCF(pot, u, tol=1e-8)
    u.Interpolate(mcf)
    assert np.allclose(u.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)


def test_2d_compound_minimization(fes_ir):
    fes = fes_ir * fes_ir
    fes_vec = fes_ir ** 2
    u = GridFunction(fes)
    du1, du2 = fes.TrialFunction()

    uvec = GridFunction(fes_vec)
    duvec = fes_vec.TrialFunction()

    du = CoefficientFunction((du1, du2))
    a = CoefficientFunction((2 / 3, 1))
    M = CoefficientFunction((2, 1 / 2, 1 / 2, 4), dims=(2, 2))

    def pot_func(u):
        return 1 / 2 * InnerProduct(M, OuterProduct(u, u)) + 4 * InnerProduct(u, a)

    def res_func(u):
        return M * u + 4 * a

    eq = res_func(du)
    eq_vec = res_func(duvec)
    check = res_func(uvec)
    pot = pot_func(duvec)

    expected = np.array([-1.11827957, -0.86021505])

    u.Interpolate(CoefficientFunction((3, 3)))
    uvec.Interpolate(CoefficientFunction((3, 3)))
    ncf = NewtonCF(eq, u, maxiter=1)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    u.Interpolate(CoefficientFunction((3, 3)))
    uvec.Interpolate(CoefficientFunction((3, 3)))
    ncf = NewtonCF(eq, u.components, maxiter=1)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec.Interpolate(CoefficientFunction((3, 3)))
    ncf = NewtonCF(eq_vec, uvec, maxiter=1)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec.Interpolate(CoefficientFunction((3, 3)))
    mcf = MinimizationCF(pot, uvec, maxiter=1)
    uvec.Interpolate(mcf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec2 = GridFunction(uvec.space)
    uvec2.Interpolate(check)
    assert np.allclose(uvec2.vec.FV().NumPy(), 0)


def test_partial_compound_minimization(fes_ir):
    # Tests the case when only some components of a space take part in minimization.
    fes = fes_ir * fes_ir * fes_ir
    fes_vec = fes_ir * fes_ir ** 2
    fes_vec2 = fes_ir ** 2

    U = GridFunction(fes)
    u_0, u_1, u_2 = U.components
    u = CoefficientFunction((u_1, u_2))
    du_0, du1, du2 = fes.TrialFunction()

    Uvec = GridFunction(fes_vec)
    uvec = Uvec.components[1]
    dUvec = fes_vec.TrialFunction()
    duvec = dUvec[1]
    uvec2 = GridFunction(fes_vec2)

    du = CoefficientFunction((du1, du2))
    a = CoefficientFunction((2 / 3, 1))
    M = CoefficientFunction((2, 1 / 2, 1 / 2, 4), dims=(2, 2))

    def pot_func(u):
        return 1 / 2 * InnerProduct(M, OuterProduct(u, u)) + 4 * InnerProduct(u, a)

    def res_func(u):
        return M * u + 4 * a

    eq = res_func(du)
    check = res_func(uvec2)
    pot = pot_func(duvec)

    expected = np.array([-1.11827957, -0.86021505])

    U.Interpolate(CoefficientFunction((0, 3, 3)))
    uvec.Interpolate(CoefficientFunction((3, 3)))
    ncf = NewtonCF(eq, u, maxiter=1)
    uvec2.Interpolate(ncf)
    assert np.allclose(uvec2.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec.Interpolate(CoefficientFunction((3, 3)))
    mcf = MinimizationCF(pot, uvec, maxiter=1)
    uvec2.Interpolate(mcf)
    assert np.allclose(uvec2.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec2.Interpolate(check)
    assert np.allclose(uvec2.vec.FV().NumPy(), 0)


def test_2d_compound_linear_nonsymmetric(fes_ir):
    fes = fes_ir * fes_ir
    u = GridFunction(fes)
    du1, du2 = fes.TrialFunction()

    fes_vec = fes_ir ** 2
    uvec = GridFunction(fes_vec)
    duvec = fes_vec.TrialFunction()

    du = CoefficientFunction((du1, du2))
    a = CoefficientFunction((2 / 3, 1))
    M = CoefficientFunction((2, 1 / 2, 1, 4), dims=(2, 2))

    def res_func(u):
        return InnerProduct(M, OuterProduct(u, u)) * (u + a) + 4 * a

    eq = res_func(du)
    eq_vec = res_func(duvec)
    check = res_func(uvec)

    expected = np.array([-0.90980601, -1.36470902])

    u.Interpolate(CoefficientFunction((-1, -1)))
    ncf = NewtonCF(eq, u, tol=1e-8)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec.Interpolate(CoefficientFunction((-1, -1)))
    ncf = NewtonCF(eq_vec, uvec, tol=1e-8)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec2 = GridFunction(uvec.space)
    uvec2.Interpolate(check)
    assert np.allclose(uvec2.vec.FV().NumPy(), 0)


def test_linear_symmetric_space_non_symmetric_system(fes_ir):
    fes_M = MatrixValued(fes_ir, dim=2, symmetric=True)

    print(fes_M.VSEmbedding())
    VS_np = fes_M.VSEmbedding().NumPy()

    expected_np = np.array([1, 2, 2, 5])

    A_np = np.array([   2,   1 / 2, 1 / 3,  0,
                        1 / 2,   4,   5 / 2,  0,
                        1 / 3, 5 / 2,   3,  4 / 3,
                        5 / 3,   2,   4 / 3,  2]).reshape((4, 4))
    b_np = A_np.dot(expected_np)

    A = CoefficientFunction(tuple(A_np.flatten().tolist()), dims=(4, 4))
    b = CoefficientFunction(tuple(b_np.flatten().tolist()))

    u = GridFunction(fes_M)
    u_trial = fes_M.TrialFunction()
    eq = A * u_trial.Reshape((4,)) - b
    u.Interpolate(CF(0) * b)
    ncf = NewtonCF(eq, u, maxiter=1)
    u.Interpolate(ncf)
    print(u.vec.FV().NumPy())
    assert np.allclose(VS_np.dot(u.vec.FV().NumPy()), expected_np, atol=1e-8, rtol=0)


def test_compound_advanced_linear_nonsymmetric_system(fes_ir):
    fes_M = MatrixValued(fes_ir, dim=3, symmetric=True)
    fes_compound = fes_ir * fes_M * (fes_ir ** 2)

    u = GridFunction(fes_compound)
    u1, u2, u3 = u.components
    du1, du2, du3 = fes_compound.TrialFunction()

    fes_vec = fes_ir ** 12
    uvec = GridFunction(fes_vec)

    cf1 = CoefficientFunction(1 / 2)
    cf2 = CoefficientFunction(tuple(range(1, 10)), dims=(3, 3))
    cf3 = CoefficientFunction((2 / 3, 3 / 4))
    u1.Interpolate(cf1)
    u2.Interpolate(1 / 2 * (cf2 + cf2.trans))
    u3.Interpolate(cf3)

    a = CoefficientFunction((2 / 3, 4 / 9))
    M22 = CoefficientFunction((2, 1 / 2,
                               1 / 6, 4), dims=(2, 2))
    M33 = CoefficientFunction((2, 1 / 2, 1 / 3,
                               1 / 2, 4, 0,
                               1 / 3, 0, 2), dims=(3, 3))

    expected_np = np.array([2,
                            3, 1, 4,
                            1, 2, 5,
                            4, 5, 1,
                            6, 2])

    A_np = np.array([
          1,  1/2,     4,     2,     0,     0,     0,     0,     0,     0,     0,     0, #1
        1/3,  3/2,     1,   4/5,     2,     5,     0,     0,     0,     0,     0,     0, #2
          5,    1,   5/2,     2,   5/3,   2/5,     5,     3,     2,     7,     0,     0, #3
          2,  4/7,     3,   4/5,   1/4,   3/8,     3,     5,     1,     5,     8,     1, #4
          0,    2,   5/3,   1/4,     2,     3,     3,     1,     6,     7,     5,     2, #5
          0,    5,   2/5,   3/8,     3,     7,     2,     4,     8,     1,     2,     1, #6
          9,    2,   1/7,     1,   5/8,   2/9,     6,     2,   1/3,     4,   5/3,     5, #7
          4,    3,   5/7,     3,   5/4,   3/9,     1,     2,   5/6,     2,   5/2,     7, #8
          1,  1/3,   5/4,   3/2,   4/5,   3/5,     0,     0,   5/2,   1/2,   3/5,     4, #9
          5,  1/5,   7/4,   3/5,     0,     8,     2,     1,   5/7,   3/2,   3/8,     0, #10
          0,  7/5,   3/2,   3/8,     1,   1/2,     0,     9,   2/7,   2/5,   7/6,   3/7, #11
          0,  1/4,     2,     7,     0,   2/3,     7,     1,   4/3,   4/9,   1/8,   8/3, #12
    ]).reshape((12, 12))

    b_np = A_np.dot(expected_np)

    A_cf = CF(tuple(A_np.flatten().tolist()), dims=(12, 12))
    b_cf = CF(tuple(b_np.flatten().tolist()))

    def res_func(u1, u2, u3):
        u_all = CF(tuple([u1] + [u2[i] for i in range(9)] + [u3[j] for j in range(2)]))
        return A_cf * u_all - b_cf

    eq = res_func(du1, du2, du3)

    uv1 = CoefficientFunction(uvec[0])
    uv2 = CoefficientFunction(tuple([uvec[i] for i in range(1, 10)]), dims=(3, 3))
    uv3 = CoefficientFunction(tuple([uvec[i] for i in range(10, 12)]))
    check = res_func(uv1, uv2, uv3)
    check_compound = res_func(u1, u2, u3)

    u1.Interpolate(cf1)
    u2.Interpolate(1 / 2 * (cf2 + cf2.trans))
    u3.Interpolate(cf3)
    ncf = NewtonCF(eq, u.components, maxiter=1)
    uvec.Interpolate(ncf)
    print(uvec.vec.FV().NumPy())
    assert np.allclose(uvec.vec.FV().NumPy(), expected_np, atol=1e-8, rtol=0)

    u1.Interpolate(uvec[0])
    u2.Interpolate(uvec[1:10])
    u3.Interpolate(uvec[10:12])

    print(u1.vec.FV().NumPy())
    print(u2.vec.FV().NumPy())
    print(u3.vec.FV().NumPy())

    uvec_check = GridFunction(uvec.space)
    uvec_check.Interpolate(check)
    print("check", uvec_check.vec.FV().NumPy())
    assert np.allclose(uvec_check.vec.FV().NumPy(), 0)

    uvec_check.Interpolate(check_compound)
    print("check_compound", uvec_check.vec.FV().NumPy())
    assert np.allclose(uvec_check.vec.FV().NumPy(), 0)

    # different starting point styles
    u1.Interpolate(cf1)
    u2.Interpolate(1 / 2 * (cf2 + cf2.trans))
    u3.Interpolate(cf3)
    ncf = NewtonCF(eq, u, maxiter=1)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected_np, atol=1e-8, rtol=0)

    u1.Interpolate(cf1)
    u2.Interpolate(1 / 2 * (cf2 + cf2.trans))
    u3.Interpolate(cf3)
    ncf = NewtonCF(eq, CoefficientFunction((u1, u2, u3)), maxiter=1)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected_np, atol=1e-8, rtol=0)

    u1.Interpolate(cf1)
    u2.Interpolate(1 / 2 * (cf2 + cf2.trans))
    u3.Interpolate(cf3)
    ncf = NewtonCF(eq, [u1, u2, u3], maxiter=1)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected_np, atol=1e-8, rtol=0)


def test_compound_advanced_nonlinear_symmetric(fes_ir):
    fes_M = MatrixValued(fes_ir, dim=3, symmetric=True)
    fes_compound = fes_ir * fes_M * (fes_ir ** 2)

    u = GridFunction(fes_compound)
    u1, u2, u3 = u.components
    du1, du2, du3 = fes_compound.TrialFunction()

    fes_vec = fes_ir ** 12
    uvec = GridFunction(fes_vec)

    d = CoefficientFunction(3)
    a = CoefficientFunction((2 / 3, 4 / 9))
    M22 = CoefficientFunction((1 / 8, 1 / 5,
                               1 / 5, 3), dims=(2, 2))
    M33 = CoefficientFunction((2, 1 / 2, 1 / 3,
                               1 / 2, 4, 1 / 2,
                               1 / 3, 1 / 2, 2), dims=(3, 3))

    wc1 = CoefficientFunction(1)
    wc2 = CoefficientFunction(1)
    wd = CoefficientFunction(50)

    def pot_func(u1, u2, u3):
        return d * (u1 ** 4 + u1 ** 2) + wc1 * u1 * Det(u2) + wd * (sqrt(Det(u2)) - 1) ** 2 + 10 * InnerProduct(u2,
                                                                                                                u2) + wc2 * InnerProduct(
            u3, u3) * Trace(u2) + InnerProduct(u3, M22 * u3) + 2 * u1 + 4 * InnerProduct(M33, u2) + InnerProduct(u3, a)

    def res_func(u1, u2, u3):
        return CoefficientFunction((
            4 * d * u1 ** 3 + 2 * d * u1 + wc1 * Det(u2) + 2,
            (wc1 * u1 * Det(u2) + 2 * wd * (sqrt(Det(u2)) - 1) * (1 / 2 * sqrt(Det(u2)))) * Inv(u2)
            + 20 * u2 + wc2 * InnerProduct(u3, u3) * Id(3) + 4 * M33,
            2 * wc2 * Trace(u2) * u3 + 2 * M22 * u3 + a
        ))

    pot = pot_func(du1, du2, du3)
    res = res_func(du1, du2, du3)

    uv1 = CoefficientFunction(uvec[0])
    uv2 = CoefficientFunction(tuple([uvec[i] for i in range(1, 10)]), dims=(3, 3))
    uv3 = CoefficientFunction(tuple([uvec[i] for i in range(10, 12)]))
    check_res = res_func(uv1, uv2, uv3)

    expected = np.array([-0.30564104, 0.60862982, -0.03132745, -0.02373416, -0.03132745,
                         0.48047082, -0.03132745, -0.02373416, -0.03132745, 0.60862982,
                         -0.17851929, -0.03970393])

    u1.Interpolate(CoefficientFunction(0))
    u2.Interpolate(Id(3))
    u3.Interpolate(CoefficientFunction((0, 0)))
    mcf = MinimizationCF(pot, u.components, tol=1e-8)
    uvec.Interpolate(mcf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    u1.Interpolate(CoefficientFunction(0))
    u2.Interpolate(Id(3))
    u3.Interpolate(CoefficientFunction((0, 0)))
    mcf = MinimizationCF(pot, u.components, tol=1e-20, rtol=1e-8)
    uvec.Interpolate(mcf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec_check = GridFunction(uvec.space)
    uvec_check.Interpolate(check_res)
    nvec = uvec_check.vec.FV().NumPy()
    allres = nvec.reshape((12, int(nvec.size / 12))).T

    assert np.allclose(allres[0][0], 0)
    assert np.allclose(allres[0][10:], 0)
    # Only the symmetric part of the error for u2 is relevant and indeed vanishes
    _res = allres[0][1:10].reshape((3, 3))
    assert np.allclose(1 / 2 * (_res + _res.T), 0)

    u1.Interpolate(CoefficientFunction(0))
    u2.Interpolate(Id(3))
    u3.Interpolate(CoefficientFunction((0, 0)))
    ncf = NewtonCF(res, u.components, tol=1e-8)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    u1.Interpolate(CoefficientFunction(0))
    u2.Interpolate(Id(3))
    u3.Interpolate(CoefficientFunction((0, 0)))
    ncf = NewtonCF(res, u.components, tol=1e-20, rtol=1e-8)
    uvec.Interpolate(ncf)
    assert np.allclose(uvec.vec.FV().NumPy(), expected, atol=1e-8, rtol=0)

    uvec_check = GridFunction(uvec.space)
    uvec_check.Interpolate(check_res)
    nvec = uvec_check.vec.FV().NumPy()
    allres = nvec.reshape((12, int(nvec.size / 12))).T
    assert np.allclose(allres[0][0], 0)

    assert np.allclose(allres[0][10:], 0)
    # Only the symmetric part of the error for u2 is relevant and indeed vanishes
    _res = allres[0][1:10].reshape((3, 3))
    assert np.allclose(1 / 2 * (_res + _res.T), 0)


if __name__ == "__main__":
    _fes_ir = mk_fes_ir()
    test_scalar_linear_minimization(_fes_ir)
    test_scalar_nonlinear_minimization(_fes_ir)
    test_2d_compound_minimization(_fes_ir)
    test_partial_compound_minimization(_fes_ir)
    test_2d_compound_linear_nonsymmetric(_fes_ir)
    test_linear_symmetric_space_non_symmetric_system(_fes_ir)
    test_compound_advanced_linear_nonsymmetric_system(_fes_ir)
    test_compound_advanced_nonlinear_symmetric(_fes_ir)
