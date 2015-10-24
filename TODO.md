# TODO:
- add token expiration checking (При выполнении методов требующих авторизации, возвратится ошибка 17: Validation required. )
- move vk auth part to separate file
- escape web chars like %20
- encrypt access token file 

- filtering special symbols in song name
- automatic detecting favourited song http://brunorocha.org/python/watching-a-directory-for-file-changes-with-python.html
- fetch vk_api parameters from config
- ask if matching is not 100%
- check if song is already added
- add song to radiostation album
- Looking for "Wes Montgomery & Milt Jackson - Delila" -> 1. Wes Montgomery - Caravan
- Looking for "054 All The People - Cramp Your Style" -> Nothing found
-  3rd song is better, but 1st added. Add song with minimum diff
    ```
    1. Rufus &amp; Chaka Khan - Feel Good
    3. Rufus - Feel good
    ```
