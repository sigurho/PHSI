import numpy as np


def time_derivative(integrator, x_dot, x_start, x_end,
                    t_start, t_end, dt, u=None, xspatial=None):
    """
    Computes the time derivative of x using the provided function *x_dot*.

    Parameters
    ----------
    integrator : str or bool
        If 'euler' or False, the time derivative at *x_start*, *t_start*
        is computed. If 'midpoint', *x_start*, *x_end*, *t_start*,
        *t_end* are used to compute the discretized implricit midpoint
        estimate of the derivative. If 'rk4', *x_start*, *t_start*, *dt*
        are used to compute the explicit Runge-Kutta 4 estimate.
        If 'srk4', *x_start*, *x_end*, *t_start*, *dt* are used to
        compute the symmetric Runge-Kutta 4 estimate.
    x_dot : callable
        Callable taking three arguments, x, t and u, returning the time
        derivative at the provided points.
    x_start : (..., N) ndarray
    x_end : (..., N) ndarray
    t_start : number or (..., 1) ndarray
    t_end : number or (..., 1) ndarray
    dt : number
    u : (..., N) ndarray, default None
        Controlled input to provide to *x_dot*. Will only be used
        if *integrator* is 'srk4'.

    Returns
    -------
    (..., N) ndarray
        The estimated time derivatives.

    Raises
    ------
    ValueError
        If the integrator type is not recognized.

    """

    integrator = (integrator.lower() if isinstance(integrator, str)
                  else integrator)
    if integrator in (False, 'euler'):
        return _time_derivative_continuous(x_dot, x_start, t_start)
    elif integrator == 'midpoint':
        x_mid = (x_end + x_start) / 2
        t_mid = (t_end + t_start) / 2
        return _time_derivative_continuous(x_dot, x_mid, t_mid)
    elif integrator == 'rk4':
        return _discrete_time_derivative_rk4(x_dot, x_start, t_start, dt, u)
    elif integrator == 'y4':
        return _discrete_time_derivative_y4(x_dot, x_start, t_start, dt, u)
    elif integrator == 'srk4':
        return _discrete_time_derivative_srk4(x_dot, x_start, x_end,
                                              t_start, dt)
    elif integrator == 'cm4':
        return _discrete_time_derivative_cm4(x_dot, x_start, x_end,
                                              t_start, dt)
    elif integrator == 'cs6':
        return _discrete_time_derivative_cs6(x_dot, x_start, x_end,
                                              t_start, dt)
    else:
        raise ValueError(f'Unknown integrator {integrator}.')


def _time_derivative_continuous(x_dot, x, t=None):
    return x_dot(x=x, t=t)


def _discrete_time_derivative_rk4(x_dot, x1, t1, dt, u):
    k1 = x_dot(x1, t1)
    k2 = x_dot(x1+.5*dt*k1, t1+.5*dt)
    k3 = x_dot(x1+.5*dt*k2, t1+.5*dt)
    k4 = x_dot(x1+dt*k3, t1+dt)
    return 1/6*(k1+2*k2+2*k3+k4)


def _discrete_time_derivative_srk4(x_dot, x1, x2, t1, dt):
    xh = (x1+x2)/2
    z1 = (1/2+np.sqrt(3)/6)*x1 + (1/2-np.sqrt(3)/6)*x2
    z2 = (1/2-np.sqrt(3)/6)*x1 + (1/2+np.sqrt(3)/6)*x2
    tm = (t1 + (1/2-np.sqrt(3)/6)*dt)
    tp = (t1 + (1/2+np.sqrt(3)/6)*dt)
    z3 = xh - np.sqrt(3)/6*dt*x_dot(z2, tp)
    z4 = xh + np.sqrt(3)/6*dt*x_dot(z1, tm)
    return 1/2*(x_dot(z3, tm)+x_dot(z4, tp))

def _discrete_time_derivative_y4(x_dot, x1, t1, dt, u): # Yoshida's 4th order method for separable systems
    M = int(x1.shape[1]/2)
    c1 = 1/(2*(2-2**(1/3)))
    c2 = (1-2**(1/3))/(2*(2-2**(1/3)))
    d1 = 1/(2-2**(1/3))
    d2 = -2**(1/3)/(2-2**(1/3))
    c = np.array([c1,c2,c2,c1])
    d = np.array([d1,d2,d1,0])
    x = x1
    for j in range(4): 
        xh = x + c[j]*dt*x_dot(x, t1)
        xn = x + d[j]*dt*x_dot(xh, t1)
        xn[:,:M] = xh[:,:M]
        x = xn
    return 1/dt*(xn-x1)

def _discrete_time_derivative_cm4(x_dot, x1, x2, t1, dt): # Cash and Moore's 4th order scheme
    xh = (x1+x2)/2
    th = t1 + 1/2*dt
    t2 = t1 + dt
    f1 = x_dot(x1, t1)
    f2 = x_dot(x2, t2)
    z = xh - dt/8*(f2-f1).detach()
    return 1/6*(f1+f2)+2/3*x_dot(z, th)

def _discrete_time_derivative_cs6(x_dot, x1, x2, t1, dt): # Cash and Singhal's 6th order scheme
    t14 = t1 + 1/4*dt
    t12 = t1 + 1/2*dt
    t34 = t1 + 3/4*dt
    t2 = t1 + dt
    f1 = x_dot(x1, t1)
    f2 = x_dot(x2, t2)
    x14 = 27/32*x1 + 5/32*x2 + dt*(9/64*f1-3/64*f2).detach()
    x34 = 5/32*x1 + 27/32*x2 + dt*(3/64*f1-9/64*f2).detach()
    x12 = (x1+x2)/2 + 5/24*dt*(f2-f1) - 2/3*dt*(x_dot(x34,t34)-x_dot(x14,t14)).detach()
    return 7/90*(f1+f2) + 16/45*(x_dot(x14,t14)+x_dot(x34,t34)) + 2/15*x_dot(x12,t12)