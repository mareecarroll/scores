"""
This module contains standard methods which may be used for continuous scoring
"""

from typing import Optional

import xarray as xr

import scores.functions
import scores.utils
from scores.processing import broadcast_and_match_nan
from scores.typing import FlexibleArrayType, FlexibleDimensionTypes, XarrayLike


def mse(
    fcst: FlexibleArrayType,
    obs: FlexibleArrayType,
    *,  # Force keywords arguments to be keyword-only
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[xr.DataArray] = None,
    is_angular: Optional[bool] = False,
) -> XarrayLike:
    """Calculates the mean squared error from forecast and observed data.

    See "Mean squared error" section at https://www.cawcr.gov.au/projects/verification/#MSE for more information

    .. math ::
        \\frac{1}{n} \\sum_{i=1}^n (\\text{forecast}_i - \\text{observed}_i)^2

    Args:
        fcst (Union[xr.Dataset, xr.DataArray, pd.Dataframe, pd.Series]):
            Forecast or predicted variables in xarray or pandas.
        obs (Union[xr.Dataset, xr.DataArray, pd.Dataframe, pd.Series]):
            Observed variables in xarray or pandas.
        reduce_dims (Union[str, Iterable[str]): Optionally specify which
            dimensions to reduce when calculating MSE. All other dimensions
            will be preserved.
        preserve_dims (Union[str, Iterable[str]): Optionally specify which
            dimensions to preserve when calculating MSE. All other dimensions
            will be reduced. As a special case, 'all' will allow all dimensions
            to be preserved. In this case, the result will be in the same
            shape/dimensionality as the forecast, and the errors will be
            the squared error at each point (i.e. single-value comparison
            against observed), and the forecast and observed dimensions
            must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)
        is_angular: specifies whether `fcst` and `obs` are angular
            data (e.g. wind direction). If True, a different function is used
            to calculate the difference between `fcst` and `obs`, which
            accounts for circularity. Angular `fcst` and `obs` data should be in
            degrees rather than radians.


    Returns:
        Union[xr.Dataset, xr.DataArray, pd.Dataframe, pd.Series]: An object containing
            a single floating point number representing the mean absolute
            error for the supplied data. All dimensions will be reduced.
            Otherwise: Returns an object representing the mean squared error,
            reduced along the relevant dimensions and weighted appropriately.
    """
    if is_angular:
        error = scores.functions.angular_difference(fcst, obs)  # type: ignore
    else:
        error = fcst - obs  # type: ignore
    squared = error * error
    squared = scores.functions.apply_weights(squared, weights=weights)  # type: ignore

    if preserve_dims or reduce_dims:
        reduce_dims = scores.utils.gather_dimensions(
            fcst.dims, obs.dims, reduce_dims=reduce_dims, preserve_dims=preserve_dims
        )

    if reduce_dims is not None:
        _mse = squared.mean(dim=reduce_dims)  # type: ignore
    else:
        _mse = squared.mean()

    return _mse


def rmse(
    fcst: FlexibleArrayType,
    obs: FlexibleArrayType,
    *,  # Force keywords arguments to be keyword-only
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[xr.DataArray] = None,
    is_angular: bool = False,
) -> FlexibleArrayType:
    """Calculate the Root Mean Squared Error

    A detailed explanation is on https://en.wikipedia.org/wiki/Root-mean-square_deviation

    .. math ::
        \\sqrt{\\frac{1}{n} \\sum_{i=1}^n (\\text{forecast}_i - \\text{observed}_i)^2}

    Args:
        fcst: Forecast
            or predicted variables in xarray or pandas.
        obs: Observed
            variables in xarray or pandas.
        reduce_dims: Optionally specify which dimensions to reduce when
            calculating RMSE. All other dimensions will be preserved.
        preserve_dims: Optionally specify which dimensions to preserve
            when calculating RMSE. All other dimensions will be reduced.
            As a special case, 'all' will allow all dimensions to be
            preserved. In this case, the result will be in the same
            shape/dimensionality as the forecast, and the errors will be
            the absolute error at each point (i.e. single-value comparison
            against observed), and the forecast and observed dimensions
            must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)
        is_angular: specifies whether `fcst` and `obs` are angular
            data (e.g. wind direction). If True, a different function is used
            to calculate the difference between `fcst` and `obs`, which
            accounts for circularity. Angular `fcst` and `obs` data should be in
            degrees rather than radians.

    Returns:
        An object containing
            a single floating point number representing the root mean squared
            error for the supplied data. All dimensions will be reduced.
            Otherwise: Returns an object representing the root mean squared error,
            reduced along the relevant dimensions and weighted appropriately.

    """
    _mse = mse(fcst, obs, reduce_dims=reduce_dims, preserve_dims=preserve_dims, weights=weights, is_angular=is_angular)

    _rmse = pow(_mse, (1 / 2))

    return _rmse  # type: ignore


def mae(
    fcst: FlexibleArrayType,
    obs: FlexibleArrayType,
    *,  # Force keywords arguments to be keyword-only
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[xr.DataArray] = None,
    is_angular: bool = False,
) -> FlexibleArrayType:
    """Calculates the mean absolute error from forecast and observed data.

    A detailed explanation is on https://en.wikipedia.org/wiki/Mean_absolute_error

    .. math ::
        \\frac{1}{n} \\sum_{i=1}^n | \\text{forecast}_i - \\text{observed}_i |

    Args:
        fcst: Forecast or predicted variables in xarray or pandas.
        obs: Observed variables in xarray or pandas.
        reduce_dims: Optionally specify which dimensions to reduce when
            calculating MAE. All other dimensions will be preserved.
        preserve_dims: Optionally specify which dimensions to preserve when
            calculating MAE. All other dimensions will be reduced. As a
            special case, 'all' will allow all dimensions to be preserved. In
            this case, the result will be in the same shape/dimensionality
            as the forecast, and the errors will be the absolute error at each
            point (i.e. single-value comparison against observed), and the
            forecast and observed dimensions must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)
        is_angular: specifies whether `fcst` and `obs` are angular
            data (e.g. wind direction). If True, a different function is used
            to calculate the difference between `fcst` and `obs`, which
            accounts for circularity. Angular `fcst` and `obs` data should be in
            degrees rather than radians.

    Returns:
        By default an xarray DataArray containing
        a single floating point number representing the mean absolute error for the
        supplied data. All dimensions will be reduced.

        Alternatively, an xarray structure with dimensions preserved as appropriate
        containing the score along reduced dimensions
    """
    if is_angular:
        error = scores.functions.angular_difference(fcst, obs)  # type: ignore
    else:
        error = fcst - obs  # type: ignore
    ae = abs(error)
    ae = scores.functions.apply_weights(ae, weights=weights)  # type: ignore

    if preserve_dims is not None or reduce_dims is not None:
        reduce_dims = scores.utils.gather_dimensions(
            fcst.dims, obs.dims, reduce_dims=reduce_dims, preserve_dims=preserve_dims
        )

    if reduce_dims is not None:
        _ae = ae.mean(dim=reduce_dims)
    else:
        _ae = ae.mean()

    # Returns unhinted types if nonstandard types passed in, but this is useful
    return _ae  # type: ignore


def mean_error(
    fcst: XarrayLike,
    obs: XarrayLike,
    *,
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[XarrayLike] = None,
) -> XarrayLike:
    """
    Calculates the mean error which is also sometimes called the additive bias.

    It is defined as

    .. math::
        \\text{mean error} =\\frac{1}{N}\\sum_{i=1}^{N}(x_i - y_i)
        \\text{where } x = \\text{the forecast, and } y = \\text{the observation}


    See "Mean error" section at https://www.cawcr.gov.au/projects/verification/ for more information

    Args:
        fcst: Forecast or predicted variables.
        obs: Observed variables.
        reduce_dims: Optionally specify which dimensions to reduce when
            calculating the mean error. All other dimensions will be preserved.
        preserve_dims: Optionally specify which dimensions to preserve when
            calculating the mean error. All other dimensions will be reduced. As a
            special case, 'all' will allow all dimensions to be preserved. In
            this case, the result will be in the same shape/dimensionality
            as the forecast, and the errors will be the error at each
            point (i.e. single-value comparison against observed), and the
            forecast and observed dimensions must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)

    Returns:
        An xarray object with the mean error of a forecast.

    """
    return additive_bias(fcst, obs, reduce_dims=reduce_dims, preserve_dims=preserve_dims, weights=weights)


def additive_bias(
    fcst: XarrayLike,
    obs: XarrayLike,
    *,
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[XarrayLike] = None,
) -> XarrayLike:
    """
    Calculates the additive bias which is also sometimes called the mean error.

    It is defined as

    .. math::
        \\text{Additive bias} =\\frac{1}{N}\\sum_{i=1}^{N}(x_i - y_i)
        \\text{where } x = \\text{the forecast, and } y = \\text{the observation}


    See "Mean error" section at https://www.cawcr.gov.au/projects/verification/ for more information

    Args:
        fcst: Forecast or predicted variables.
        obs: Observed variables.
        reduce_dims: Optionally specify which dimensions to reduce when
            calculating the additive bias. All other dimensions will be preserved.
        preserve_dims: Optionally specify which dimensions to preserve when
            calculating the additive bias. All other dimensions will be reduced. As a
            special case, 'all' will allow all dimensions to be preserved. In
            this case, the result will be in the same shape/dimensionality
            as the forecast, and the errors will be the error at each
            point (i.e. single-value comparison against observed), and the
            forecast and observed dimensions must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)

    Returns:
        An xarray object with the additive bias of a forecast.

    """
    # Note - mean error call this function
    error = fcst - obs
    score = scores.functions.apply_weights(error, weights=weights)
    reduce_dims = scores.utils.gather_dimensions(
        fcst.dims, obs.dims, reduce_dims=reduce_dims, preserve_dims=preserve_dims
    )
    score = score.mean(dim=reduce_dims)
    return score  # type: ignore


def multiplicative_bias(
    fcst: XarrayLike,
    obs: XarrayLike,
    *,
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[XarrayLike] = None,
) -> XarrayLike:
    """
    Calculates the multiplicative bias.

    Most suited for forecasts that have a lower bound at 0 such as wind speed. Will return
    a np.inf where the mean of `obs` across the dims to be reduced is 0.
    It is defined as

    .. math::
        \\text{{Multiplicative bias}} = \\frac{\\frac{1}{N}\\sum_{i=1}^{N}x_i}{\\frac{1}{N}\\sum_{i=1}^{N}y_i}
        \\text{where } x = \\text{the forecast, and } y = \\text{the observation}

    See "(Multiplicative) bias" section at https://www.cawcr.gov.au/projects/verification/ for more information

    Args:
        fcst: Forecast or predicted variables.
        obs: Observed variables.
        reduce_dims: Optionally specify which dimensions to reduce when
            calculating the multiplicative bias. All other dimensions will be preserved.
        preserve_dims: Optionally specify which dimensions to preserve when
            calculating the multiplicative bias. All other dimensions will be reduced. As a
            special case, 'all' will allow all dimensions to be preserved. In
            this case, the result will be in the same shape/dimensionality
            as the forecast, and the errors will be the error at each
            point (i.e. single-value comparison against observed), and the
            forecast and observed dimensions must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)

    Returns:
        An xarray object with the multiplicative bias of a forecast.

    """
    reduce_dims = scores.utils.gather_dimensions(
        fcst.dims, obs.dims, reduce_dims=reduce_dims, preserve_dims=preserve_dims
    )
    fcst = scores.functions.apply_weights(fcst, weights=weights)
    obs = scores.functions.apply_weights(obs, weights=weights)

    # Need to broadcast and match NaNs so that the fcst mean and obs mean are for the
    # same points
    fcst, obs = broadcast_and_match_nan(fcst, obs)
    multi_bias = fcst.mean(dim=reduce_dims) / obs.mean(dim=reduce_dims)
    return multi_bias


def pbias(
    fcst: XarrayLike,
    obs: XarrayLike,
    *,
    reduce_dims: Optional[FlexibleDimensionTypes] = None,
    preserve_dims: Optional[FlexibleDimensionTypes] = None,
    weights: Optional[XarrayLike] = None,
) -> XarrayLike:
    """
    Calculates the percent bias, which is the ratio of the additive bias to the mean observed value, multiplied by 100.

    Percent bias is used for evaluating and comparing forecast accuracy across stations or dataset with varying magnitudes.
    By expressing the error as a percentage of the observed value, it allows for standardized comparisons, enabling assessment
    of forecast performance regardless of the absolute scale of values. Like multiplicative_bias, Percent bias will return a np.inf
    where the mean of `obs` across the dims to be reduced is 0.
    It is defined as

    .. math::
        \\text{Percent bias} = 100 * \\frac{\\sum_{i=1}^{N}(x_i - y_i)}{\\sum_{i=1}^{N} y_i}

    where:
        - :math:`x_i` = the values of x in a sample (i.e. forecast values)
        - :math:`y_i` = the values of y in a sample (i.e. observed values)

    See "pbias" section at https://search.r-project.org/CRAN/refmans/hydroGOF/html/pbias.html for more information

    Args:
        fcst: Forecast or predicted variables.
        obs: Observed variables.
        reduce_dims: Optionally specify which dimensions to reduce when
            calculating the percentage additive bias. All other dimensions will be preserved.
        preserve_dims: Optionally specify which dimensions to preserve when
            calculating the additive bias percentage. All other dimensions will be reduced. As a
            special case, 'all' will allow all dimensions to be preserved. In
            this case, the result will be in the same shape/dimensionality
            as the forecast, and the errors will be the error at each
            point (i.e. single-value comparison against observed), and the
            forecast and observed dimensions must match precisely.
        weights: Optionally provide an array for weighted averaging (e.g. by area, by latitude,
            by population, custom)

    Returns:
        An xarray object with the percent bias of a forecast.

    References:
        -   Sorooshian, S., Duan, Q., & Gupta, V. K. (1993). Calibration of rainfall-runoff models:
            Application of global optimization to the Sacramento Soil Moisture Accounting Model.
            Water Resources Research, 29(4), 1185-1194. https://doi.org/10.1029/92WR02617
        -   Alfieri, L., Pappenberger, F., Wetterhall, F., Haiden, T., Richardson, D., & Salamon, P. (2014).
            Evaluation of ensemble streamflow predictions in Europe. Journal of Hydrology, 517, 913-922.
            http://dx.doi.org/10.1016/j.jhydrol.2014.06.035
        -   Dawson, C. W., Abrahart, R. J., & See, L. M. (2007). HydroTest:
            A web-based toolbox of evaluation metrics for the standardised assessment of hydrological forecasts.
            Environmental Modelling and Software, 22(7), 1034-1052.
            https://doi.org/10.1016/j.envsoft.2006.06.008
        -   Moriasi, D. N., Arnold, J. G., Van Liew, M. W., Bingner, R. L., Harmel, R. D., & Veith, T. L. (2007).
            Model evaluation guidelines for systematic quantification of accuracy in watershed simulations.
            Transactions of the ASABE, 50(3), 885-900. https://doi.org/10.13031/2013.23153




    """
    reduce_dims = scores.utils.gather_dimensions(
        fcst.dims, obs.dims, reduce_dims=reduce_dims, preserve_dims=preserve_dims
    )
    fcst = scores.functions.apply_weights(fcst, weights=weights)
    obs = scores.functions.apply_weights(obs, weights=weights)

    # Need to broadcast and match NaNs so that the mean error and obs mean are for the
    # same points
    fcst, obs = broadcast_and_match_nan(fcst, obs)
    error = fcst - obs

    _pbias = 100 * error.mean(dim=reduce_dims) / obs.mean(dim=reduce_dims)
    return _pbias
