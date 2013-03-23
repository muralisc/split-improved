/* App Module */
//replace the angular js markers as they conflict with Django template markers
angular.module('YourAppName', ['$strap.directives'], function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
    $interpolateProvider.endSymbol('}]}');
});
