// app.js

const { useState,useEffect } = React;
//todo meter esto en una variable de entorno (Nombre del servicio, y el puerto)
const API_URL = 'http://localhost:5005';

function App() {
  // Estado para controlar la pantalla actual
  const [screen, setScreen] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Validar campos en blanco
  const validateFields = () => {
    if (username === '' || password === '') {
      setErrorMessage('Please fill in all fields.');
      return false;
    }
    setErrorMessage('');
    return true;
  };

  const handleScreenChange = (newScreen) => {
    setScreen(newScreen);
  };

  // Manejar login
  const handleLogin = async () => {
    if (!validateFields()) return;
  
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });
  
    const result = await response.json();
    if (result.status === 'Inicio de sesión exitoso') {
      // Guardar el username en localStorage
      localStorage.setItem('username', username);
      handleScreenChange('ask'); // Cambiar pantalla después de login exitoso
    } else {
      alert("Wrong credentials")
      setErrorMessage('Invalid login credentials.');
    }
  };
  
  

  // Manejar registro
  const handleRegister = async () => {
    if (!validateFields()) return;

    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (result.status === 'Usuario registrado con éxito') {
      alert('User registered successfully!');
    } else {
      setErrorMessage('Registration failed.');
    }
  };

  const handleLogout = () => {
    setUsername('');
    setPassword('');
    handleScreenChange('login');
  };
  const handleAsk = async () => {
    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: updatedPrompt })
      });

      const result = await response.json();
      if (response.status === 200) {
        setAskResults(result);
      } else {
        setAskError(result.error || 'Error during ask request.');
      }
    } catch (error) {
      setAskError('Error occurred while making the ask request.');
    }
  };

  const handleUpdatePrompt = async () => {
    try {
      const response = await fetch(`${API_URL}/updatePrompt/${selectedPromptId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: updatedPrompt })
      });

      const result = await response.json();
      if (result.status === 'Prompt updated successfully') {
        alert('Prompt updated!');
        setPrompts(prompts.map(prompt => prompt.id === selectedPromptId ? { ...prompt, prompt: updatedPrompt } : prompt));
        setShowSubMenu(false); // Cerrar el submenú después de actualizar
      } else {
        alert('Failed to update prompt.');
      }
    } catch (error) {
      console.error('Error updating prompt:', error);
    }
  };

  const closeSubMenu = () => {
    setShowSubMenu(false);
    setAskResults([]);
    setAskError(null);
  };
  return (
    <div className="container">
      <h1 className="title">Song Prompt App</h1>
      {screen === 'login' ? (
        // Pantalla de inicio de sesión/registro
        <div className="section">
          <h2>Login or Register</h2>
          <input
            type="text"
            placeholder="Enter your username..."
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Enter your password..."
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="button" onClick={handleLogin}>
            Login
          </button>
          <button className="button" onClick={handleRegister}>
            Register
          </button>
        </div>
      ) : (
        // Pantalla principal de la aplicación
        <div>
          {/* Barra de navegación */}
          <nav className="nav">
            <button className="button" onClick={() => handleScreenChange('ask')}>Ask</button>
            <button className="button" onClick={() => handleScreenChange('search')}>Search Prompts</button>
            <button className="button" onClick={() => handleScreenChange('findFriends')}>Find Friends</button>
            <button className="button" onClick={() => handleScreenChange('Friends')}>Friends</button>
            <button className="button" onClick={() => handleScreenChange('feed')}>Feed</button>
            <button className="button" onClick={() => handleScreenChange('me')}>Me</button>
          </nav>
          {/* Contenido de la pantalla seleccionada */}
          <div className="content">
            {screen === 'ask' && <Ask />}
            {screen === 'search' && <SearchPrompts />}
            {screen === 'findFriends' && <FindFriends />}
            {screen === 'Friends' && <Friends />}
            {screen === 'feed' && <Feed />}
            {screen === 'me' && <Me onLogout={handleLogout} />}
          </div>
        </div>
      )}
    </div>
  );
}

// Componentes individuales para cada sección de la UI
// TODO CAMBIAR EL LOCAL HOST POR LAS VARIABLES DEL NODEPORT DE LA API

function Ask() {
  const [prompt, setPrompt] = useState('');
  const [results, setResults] = useState([]);

  const handleAsk = async () => {
    // Enviar el prompt a la ruta /ask de tu API Flask para realizar la búsqueda
    const response = await fetch(API_URL+'/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: prompt,  // Enviar el prompt como 'question' en JSON
      }),
    });

    // Parsear la respuesta JSON
    const result = await response.json();
    
    // Asignar los resultados a tu estado de resultados
    setResults(result);
  };

  const handleSubmitPrompt = async () => {
    const username = localStorage.getItem('username');
    const response = await fetch(API_URL+'/publish', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',  // Cambiar a application/json
      },
      body: JSON.stringify({
        username: username,
        prompt: prompt,
      }),
    });
  
    const result = await response.json();
    if (result.status === "Prompt publicado con éxito") {
      alert("¡Prompt publicado con éxito!");
    }
  };

  return (
    <div className="section">
      <h2>Ask a Song Prompt</h2>
      <input
        type="text"
        placeholder="Type your question here..."
        className="input"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      
      {/* Botón Ask */}
      <button className="button" onClick={handleAsk}>Ask</button>
      
      {/* Botón Submit para publicar el prompt */}
      <button className="button" onClick={handleSubmitPrompt}>Submit</button>

      {/* Mostrar los resultados de la búsqueda */}
      <div className="results">
        {results.length > 0 ? (
          results.map((result, index) => (
            <div key={index} className="result-item">
              <p><strong>Canción:</strong> {result.name || "Unknown Song"}</p>
              <p><strong>Artistas:</strong> {result.artists || "Unknown Artist"}</p>
              <p><strong>Letras:</strong> {result.lyrics || "No lyrics available"}</p>
              <hr />
            </div>
          ))
        ) : (
          <p>No results found</p>
        )}
      </div>
    </div>
  );
}

function SearchPrompts() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    const response = await fetch(API_URL + `/search?keyword=${encodeURIComponent(searchTerm)}`);
    const result = await response.json();

    if (result.results) {
      setResults(result.results);
    } else {
      setResults([]);
    }
  };

  const handleLike = async (promptId, index) => {
    const username = localStorage.getItem('username');  // Obtener el username del usuario logueado
    
    const response = await fetch(API_URL + '/like', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',  // Cambiar el tipo de contenido a JSON
      },
      body: JSON.stringify({
        username: username,  // Enviar el username en lugar de user_id
        prompt_id: promptId,  // ID del prompt que fue liked
      }),
    });

    const result = await response.json();
    
    if (result.status === 'Prompt liked successfully') {
      alert('Prompt liked!');
      
      // Actualizar el contador de likes en el frontend (si la API también incrementa los likes)
      const updatedResults = [...results];
      updatedResults[index].likes += 1;  // Incrementar el número de likes localmente
      setResults(updatedResults);
    } else {
      alert('You have already liked this post');
    }
  };

  return (
    <div className="section">
      <h2>Search Prompts</h2>
      <input
        type="text"
        placeholder="Search..."
        className="input"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button className="button" onClick={handleSearch}>Search</button>

      <div className="results">
        {results.length > 0 ? (
          results.map((res, index) => (
            <div key={index} className="result-item">
              <p><strong>Prompt ID:</strong> {res.id}</p>
              <p><strong>Username:</strong> {res.username}</p>
              <p><strong>Prompt:</strong> {res.prompt}</p>
              <p><strong>Date:</strong> {res.date}</p>
              <p><strong>Likes:</strong> {res.likes}</p>  {/* Mostrar los likes */}
              <button className="button" onClick={() => handleLike(res.id, index)}>Like</button>
              <hr />
            </div>
          ))
        ) : (
          <p>No prompts found</p>
        )}
      </div>
    </div>
  );
}
function SearchPrompts() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [askResults, setAskResults] = useState([]);  // Para almacenar los resultados de Ask
  const [selectedPrompt, setSelectedPrompt] = useState(null);  // Para manejar el prompt seleccionado
  const [askError, setAskError] = useState(null); 
  const handleSearch = async () => {
    const response = await fetch(API_URL + `/search?keyword=${encodeURIComponent(searchTerm)}`);
    const result = await response.json();

    if (result.results) {
      setResults(result.results);
    } else {
      setResults([]);
    }
  };

  const handleLike = async (promptId, index) => {
    const username = localStorage.getItem('username');
    
    // Verificar que ambos datos estén presentes
    if (!username || !promptId) {
      console.error('Username or promptId is missing:', { username, promptId });
      alert('Error: Missing data.');
      return;
    }
  
    try {
      const response = await fetch(`${API_URL}/like`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          prompt_id: promptId,
        }),
      });
  
      // Verificar si la respuesta fue exitosa
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error from API:', errorData);
        throw new Error('Error from the API');
      }
  
      const result = await response.json();
      console.log(result); // Verificar qué devuelve el backend
  
      if (result.status === "Prompt liked and republished successfully") {
        alert('Prompt liked!');
  
        // Actualizar el número de likes con el valor devuelto por la API
        const updatedResults = results.map((prompt, i) => 
          i === index ? { ...prompt, likes: result.updated_likes } : prompt
        );
  
        // Actualizar el estado con el nuevo array de resultados
        setResults(updatedResults);
      } else {
        alert(result.error || 'Error liking prompt');
      }
    } catch (error) {
      console.error('Error in the like process:', error);  // Mostramos el error en la consola
      alert('An error occurred while liking the prompt.');
    }
  };
  

  const handleAsk = async (prompt) => {
    setSelectedPrompt(prompt);  // Guardar el prompt seleccionado
    setAskError(null);  // Limpiar errores previos
    setAskResults([]);  // Limpiar los resultados anteriores

    try {
      const response = await fetch(API_URL + '/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: prompt.prompt,  // Enviar la pregunta del prompt al backend
        }),
      });

      const result = await response.json();

      if (response.status === 200) {
        setAskResults(result);  // Almacenar los resultados de la búsqueda
      } else {
        setAskError(result.error || 'Error during ask request.');
      }
    } catch (error) {
      setAskError('Error occurred while making the ask request.');
    }
  };

  const closeModal = () => {
    setSelectedPrompt(null);
    setAskResults([]);
    setAskError(null);
  };

  return (
    <div className="section">
      <h2>Search Prompts</h2>
      <input
        type="text"
        placeholder="Search..."
        className="input"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button className="button" onClick={handleSearch}>Search</button>

      <div className="results">
        {results.length > 0 ? (
          results.map((res, index) => (
            <div key={index} className="result-item">
              <p><strong>Prompt ID:</strong> {res.id}</p>
              <p><strong>Username:</strong> {res.username}</p>
              <p><strong>Prompt:</strong> {res.prompt}</p>
              <p><strong>Date:</strong> {res.date}</p>
              <p><strong>Likes:</strong> {res.likes}</p>
              <button className="button" onClick={() => handleLike(res.id, index)}>Like</button>
              <button className="button ask-button" onClick={() => handleAsk(res)}>Ask</button> {/* Botón para hacer Ask */}
              <hr />
            </div>
          ))
        ) : (
          <p>No prompts found</p>
        )}
      </div>

      {/* Modal para mostrar los resultados del Ask */}
      {selectedPrompt && (
      <div className="modal-overlay">
        <div className="modal">
          <h3>Results for: {selectedPrompt.prompt}</h3>
          {askError ? (
            <p style={{ color: 'red' }}>{askError}</p>
          ) : (
            <div className="ask-results">
              {askResults.length > 0 ? (
                askResults.map((result, index) => (
                  <div key={index} className="ask-result-item card">
                    <h4 className="card-title">{result.name}</h4> {/* Estilo de título para la canción */}
                    <p><strong>Artists:</strong> {result.artists}</p>
                    <p><strong>Lyrics:</strong> {result.lyrics}</p>
                  </div>
                ))
              ) : (
                <p>No results found for this prompt.</p>
              )}
            </div>
          )}
          <button className="button close-button" onClick={closeModal}>Close</button>
        </div>
      </div>
    )}
    </div>
  );
}


function PromptItem({ promptId, promptText }) {
  const handleLike = async () => {
    const username = localStorage.getItem('username');  // Obtener el username del usuario logueado
    const response = await fetch(API_URL + '/like', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,  // Enviar el username
        prompt_id: promptId,  // Enviar el ID del prompt
      }),
    });
    const result = await response.json();
    if (result.error) {
      alert(result.error);  // Mostrar error si el usuario ya ha dado "like"
    } else {
      alert("Prompt liked successfully!");
    }
  };

  return (
    <div>
      <p>{promptText}</p>
      <button onClick={handleLike}>Like</button>
    </div>
  );
}



function FindFriends() {
  const [users, setUsers] = useState([]);
  const [searchId, setSearchId] = useState('');
  const [foundUser, setFoundUser] = useState(null);
  const [messageVisible, setMessageVisible] = useState(false);
  const username = localStorage.getItem('username');

  // Fetch random users when the component loads
  useEffect(() => {
    fetch(API_URL + '/friends/random')
      .then(response => response.json())
      .then(data => {
        if (data.users.length === 0) {
          setMessageVisible(true);  // Show hidden message if no users
        } else {
          setUsers(data.users);  // Store users (array of strings) in state
        }
      })
      .catch(err => {
        console.error("Error fetching users:", err);
        setMessageVisible(true);
      });
  }, []);

  const handleFollow = async (followeeUsername) => {
    // Handle follow functionality
    const response = await fetch(API_URL + '/follow', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        follower_username: username,  // The logged-in user's username
        followee_username: followeeUsername,  // The username of the user to follow
      }),
    });

    const result = await response.json();
    if (result.status === 'Follow successful') {
      alert('You are now following this user!');
    }else{
      alert('You already follow this user');
    }
  };

  const handleSearch = async () => {
    try {
      // Cambiar el parámetro de 'id' a 'username' en la URL
      const response = await fetch(API_URL + `/friends/search?username=${encodeURIComponent(searchId)}`);
      
      if (response.status === 404) {
        setFoundUser(null);
        alert('User not found');
        return;
      }
      
      const result = await response.json();
      setFoundUser(result.user || null);  // Guardar el usuario encontrado en el estado
    } catch (error) {
      console.error("Error fetching user:", error);
      alert('An error occurred while searching for the user.');
    }
  };

  return (
    <div className="section">
      <h2>Find Friends</h2>

      {/* Search for a user by username */}
      <input
        type="text"
        placeholder="Search by ID..."
        className="input"
        value={searchId}
        onChange={(e) => setSearchId(e.target.value)}
      />
      <button className="button" onClick={handleSearch}>Search</button>

      {foundUser && (
        <div className="result-item">
          <p><strong>Username:</strong> {foundUser.username}</p>
          <button className="button" onClick={() => handleFollow(foundUser.username)}>Follow</button>
        </div>
      )}

      {/* Display random users */}
      <div className="results">
        {users.map((username, index) => (
          <div key={index} className="result-item">
            <p><strong>Username:</strong> {username}</p>
            <button className="button" onClick={() => handleFollow(username)}>Follow</button>
            <hr />
          </div>
        ))}
      </div>

      {/* Hidden message if no users are available */}
      {messageVisible && (
        <p>Vaya, nadie se ha registrado aún a esta increíble red social :(</p>
      )}
    </div>
  );
}

function Friends() {  
  const [friends, setFriends] = useState([]);
  const [message, setMessage] = useState("No friends added yet.");
  
  useEffect(() => {
    const username = localStorage.getItem('username');  // Obtener el nombre del usuario logueado

    if (!username) {
      setMessage('You need to log in to see your friends.');
      return;
    }

    // Hacer la solicitud al backend para obtener la lista de amigos
    fetch(`${API_URL}/friends?follower_id=${username}`)
      .then(response => response.json())
      .then(data => {
        if (data.friends && data.friends.length > 0) {
          setFriends(data.friends);
        } else {
          setMessage('No friends found.');
        }
      })
      .catch(err => {
        console.error('Error fetching friends:', err);
        setMessage('Failed to load friends.');
      });
  }, []);

  return (
    <div className="section">
      <h2>Your Friends</h2>
      {friends.length > 0 ? (
        <div className="friends-grid">
          {friends.map(friend => (
            <div key={friend.username} className="friend-card">
              <div className="friend-info">
                <h3>{friend.username}</h3>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>{message}</p>
      )}
    </div>
  );
}

function Feed() {
  const [prompts, setPrompts] = useState([]);
  const [message, setMessage] = useState('No prompts to show yet!');
  const [askResults, setAskResults] = useState([]);  // Para almacenar los resultados del Ask
  const [selectedPrompt, setSelectedPrompt] = useState(null);  // Para manejar el prompt seleccionado
  const [askError, setAskError] = useState(null);  // Para manejar errores del Ask

  useEffect(() => {
    const username = localStorage.getItem('username');  // Obtener el nombre del usuario logueado

    if (!username) {
      setMessage('You need to log in to see the feed.');
      return;
    }

    // Hacer la solicitud al backend para obtener el feed
    fetch(`${API_URL}/feed?username=${username}`)
      .then(response => response.json())
      .then(data => {
        if (data.feed && data.feed.length > 0) {
          setPrompts(data.feed);  // Cambiar el campo a "feed"
        } else {
          setMessage('No prompts to show yet!');
        }
      })
      .catch(err => {
        console.error('Error fetching feed:', err);
        setMessage('Failed to load the feed.');
      });
  }, []);

  const handleLike = async (prompt, index) => {
    const username = localStorage.getItem('username');
    
    // Verificar que ambos datos estén presentes
    if (!username || !prompt.id) {
      console.error('Username or promptId is missing:', { username, prompt });
      alert('Error: Missing data.');
      return;
    }
  
    try {
      const response = await fetch(`${API_URL}/like`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          prompt_id: prompt.id,  // Enviar el ID del prompt
        }),
      });
  
      // Verificar si la respuesta fue exitosa
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error from API:', errorData);
        throw new Error('Error from the API');
      }
  
      const result = await response.json();
      console.log(result); // Verificar qué devuelve el backend
  
      if (result.status === "Prompt liked and republished successfully") {
        alert('Prompt liked!');
  
        // Actualizar el número de likes con el valor devuelto por la API
        const updatedPrompts = prompts.map((p, i) => 
          i === index ? { ...p, likes: result.updated_likes } : p
        );
  
        // Actualizar el estado con el nuevo array de prompts
        setPrompts(updatedPrompts);
      } else {
        alert(result.error || 'Error liking prompt');
      }
    } catch (error) {
      console.error('Error in the like process:', error);  // Mostramos el error en la consola
      alert('An error occurred while liking the prompt.');
    }
  };
  
  
  
  
  const handleAsk = async (prompt) => {
    setSelectedPrompt(prompt);
    setAskError(null);
    setAskResults([]);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: prompt.prompt,  // Enviar la pregunta del prompt al backend
        }),
      });

      const result = await response.json();

      if (response.status === 200) {
        setAskResults(result);  // Almacenar los resultados de la búsqueda
      } else {
        setAskError(result.error || 'Error during ask request.');
      }
    } catch (error) {
      setAskError('Error occurred while making the ask request.');
    }
  };

  const closeModal = () => {
    setSelectedPrompt(null);  // Cerrar el modal
    setAskResults([]);  // Limpiar los resultados
    setAskError(null);  // Limpiar el error
  };

  return (
    <div className="section">
      <h2>Feed</h2>
      {prompts.length > 0 ? (
        <div className="feed-list">
          {prompts.map((prompt, index) => (
            <div key={`${prompt.username}-${prompt.date}`} className="feed-item">
              <h3>{prompt.username}</h3>
              <p>{prompt.prompt}</p>
              <p><strong>Date:</strong> {new Date(prompt.date).toLocaleString()}</p>
              <p><strong>Likes:</strong> {prompt.likes}</p>
              <button className="button" onClick={() => handleLike(prompt, index)}>Like</button>
              <button className="button ask-button" onClick={() => handleAsk(prompt)}>Ask</button>
            </div>
          ))}
        </div>
      ) : (
        <p>{message}</p>
      )}

      {/* Modal para mostrar los resultados del Ask */}
      {selectedPrompt && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal">
            <button className="close-modal" onClick={closeModal}>×</button>
            <h3>Results for: {selectedPrompt.prompt}</h3>
            {askError ? (
              <p style={{ color: 'red' }}>{askError}</p>
            ) : (
              <div className="ask-results">
                {askResults.length > 0 ? (
                  askResults.map((result, index) => (
                    <div key={index} className="ask-result-item card">
                      <h4 className="card-title">{result.name}</h4>
                      <p><strong>Artists:</strong> {result.artists}</p>
                      <p><strong>Lyrics:</strong> {result.lyrics}</p>
                    </div>
                  ))
                ) : (
                  <p>No results found for this prompt.</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


function Me({ onLogout }) {
  const [username, setUsername] = useState('');
  const [prompts, setPrompts] = useState([]);
  const [newPassword, setNewPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [message, setMessage] = useState('');
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [askResults, setAskResults] = useState([]);
  const [askError, setAskError] = useState(null);
  const [showSubMenu, setShowSubMenu] = useState(false);
  const [selectedPromptId, setSelectedPromptId] = useState(null);
  const [updatedPrompt, setUpdatedPrompt] = useState('');

  useEffect(() => {
    const storedUsername = localStorage.getItem('username');
    setUsername(storedUsername);

    fetch(`${API_URL}/me/getMyPrompts?username=${storedUsername}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.results && data.results.length > 0) {
          setPrompts(data.results);
        } else {
          setMessage('No prompts added yet.');
        }
      })
      .catch(err => {
        console.error('Error fetching user prompts:', err);
        setMessage('Failed to load prompts.');
      });
  }, []);
  const handleAsk = async () => {
    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: updatedPrompt })
      });

      const result = await response.json();
      if (response.status === 200) {
        setAskResults(result);
      } else {
        setAskError(result.error || 'Error during ask request.');
      }
    } catch (error) {
      setAskError('Error occurred while making the ask request.');
    }
  };
  const handleAskForPrompt = (prompt) => {
    setSelectedPrompt(prompt);  // Guardar el prompt seleccionado para mostrar los resultados de Ask
    setAskError(null);
    setAskResults([]);
  
    // Hacer la solicitud de Ask para el prompt seleccionado
    fetch(`${API_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question: prompt.prompt })  // Usar el texto del prompt directamente
    })
      .then(response => response.json())
      .then(result => {
        if (result.error) {
          setAskError(result.error);
        } else {
          setAskResults(result);
        }
      })
      .catch(err => {
        console.error('Error in ask request:', err);
        setAskError('An error occurred while making the ask request.');
      });
  };
  const handleUpdatePrompt = async () => {
    try {
      const response = await fetch(`${API_URL}/updatePrompt/${selectedPromptId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: updatedPrompt })
      });

      const result = await response.json();
      if (result.status === 'Prompt updated successfully') {
        alert('Prompt updated!');
        setPrompts(prompts.map(prompt => prompt.id === selectedPromptId ? { ...prompt, prompt: updatedPrompt } : prompt));
        setShowSubMenu(false); // Cerrar el submenú después de actualizar
      } else {
        alert('Failed to update prompt.');
      }
    } catch (error) {
      console.error('Error updating prompt:', error);
    }
  };
  const handleDeletePrompt = async (promptId) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this prompt?");
    if (!confirmDelete) return;

    try {
        // Hacer la solicitud DELETE al backend usando el ID del prompt
        const response = await fetch(`${API_URL}/deletePrompts/${promptId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const result = await response.json();
        if (result.status === 'Prompt and associated likes deleted successfully') {
            alert('Prompt deleted!');
            // Actualizar la lista de prompts en el frontend eliminando el prompt borrado
            setPrompts(prompts.filter(prompt => prompt.id !== promptId));
        } else {
            alert('Failed to delete the prompt.');
        }
    } catch (error) {
        console.error('Error deleting the prompt:', error);
    }
};
const handleEditPrompt = (promptId, newPrompt) => {
  setShowSubMenu(true);
  setSelectedPromptId(promptId);
  setUpdatedPrompt(newPrompt);
};
const closeSubMenu = () => {
  setShowSubMenu(false);
  setAskResults([]);
  setAskError(null);
};

  const closeModal = () => {
    setSelectedPrompt(null);
    setAskResults([]);
    setAskError(null);
  };
  const handleChangePassword = async () => {
    if (!newPassword || !currentPassword) return alert('Please enter your current and new password');

    const response = await fetch(`${API_URL}/me/updatePassword`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,
        password: currentPassword,
        newPassword: newPassword,
      }),
    });

    const result = await response.json();
    if (result.status === 'Usuario registrado con éxito') {
      alert('Password changed successfully!');
      setNewPassword('');
      setCurrentPassword('');
    } else {
      alert('Failed to change password.');
    }
  };

  const handleChangeUsername = async () => {
    if (!newUsername || !currentPassword) {
      return alert('Please enter your new username and current password');
    }
  
    const response = await fetch(`${API_URL}/me/updateUsername`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,           // Asegúrate de que este valor esté correctamente definido
        password: currentPassword,    // Contraseña actual
        newUsername: newUsername,     // Nuevo nombre de usuario
      }),
    });
  
    const result = await response.json();
    if (result.status === 'Usuario registrado con éxito') {
      alert('Username changed successfully!');
      localStorage.setItem('username', newUsername);
      setUsername(newUsername);
      setNewUsername('');
    } else {
      alert(result.error || 'Failed to change username.');
    }
  };

  return (
    <div className="me-section">
      <h2 className="me-title">My Profile</h2>
      <div className="me-details">
        <p><strong>Username:</strong> {username}</p>
      </div>

      <div className="me-form">
        <h3>Change Password</h3>
        <div className="input-group">
          <input
            type="password"
            placeholder="Current Password"
            className="input"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
        <div className="input-group">
          <input
            type="password"
            placeholder="New Password"
            className="input"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </div>
        <button className="button" onClick={handleChangePassword}>Change Password</button>
      </div>

      <div className="me-form">
        <h3>Change Username</h3>
        <div className="input-group">
          <input
            type="text"
            placeholder="New Username"
            className="input"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
          />
        </div>
        <div className="input-group">
          <input
            type="password"
            placeholder="Current Password"
            className="input"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </div>
        <button className="button" onClick={handleChangeUsername}>Change Username</button>
      </div>

      <button className="button logout-button" onClick={onLogout}>Logout</button>

      <div className="my-prompts">
        <h3>My Prompts</h3>
        {prompts.length > 0 ? (
          <ul className="prompt-list">
            {prompts.map((prompt, index) => (
              <li key={index} className="prompt-item card">
                <p>{prompt.prompt}</p>
                <p><strong>Date:</strong> {new Date(prompt.date).toLocaleString()}</p>
                <p><strong>Likes:</strong> {prompt.likes}</p>
                <button className="button ask-button" onClick={() => handleAskForPrompt(prompt)}>Ask</button>
                <button className="button delete-button" onClick={() => handleDeletePrompt(prompt.id)}>Delete</button>
                <button className="button edit-button" onClick={() => handleEditPrompt(prompt.id, prompt.prompt)}>Edit</button>
              </li>
            ))}
          </ul>
        ) : (
          <p>{message}</p>
        )}
      </div>
{/* Submenú Modal */}
{showSubMenu && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Edit Prompt</h3>
            <textarea
              value={updatedPrompt}
              onChange={(e) => setUpdatedPrompt(e.target.value)}
            />
            
            {/* Botones del Submenú */}
            <div className="modal-buttons">
              <button className="button ask-button" onClick={handleAsk}>Ask</button>
              <button className="button update-button" onClick={handleUpdatePrompt}>Update</button>
              <button className="button cancel-button" onClick={closeSubMenu}>Cancel</button>
            </div>

            {/* Resultados de Ask */}
            {askError ? (
              <p style={{ color: 'red' }}>{askError}</p>
            ) : (
              <div className="ask-results">
                {askResults.length > 0 ? (
                  askResults.map((result, index) => (
                    <div key={index} className="ask-result-item">
                      <p><strong>Song:</strong> {result.name}</p>
                      <p><strong>Artists:</strong> {result.artists}</p>
                      <p><strong>Lyrics:</strong> {result.lyrics}</p>
                    </div>
                  ))
                ) : (
                  <p>No ask results found for this prompt.</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      {/* Modal for Ask Results */}
      {selectedPrompt && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal">
            <button className="close-modal" onClick={closeModal}>×</button>
            <h3>Results for: {selectedPrompt.prompt}</h3>
            {askError ? (
              <p style={{ color: 'red' }}>{askError}</p>
            ) : (
              <div className="ask-results">
                {askResults.length > 0 ? (
                  askResults.map((result, index) => (
                    <div key={index} className="ask-result-item card">
                      <h4 className="card-title">{result.name}</h4>
                      <p><strong>Artists:</strong> {result.artists}</p>
                      <p><strong>Lyrics:</strong> {result.lyrics}</p>
                    </div>
                  ))
                ) : (
                  <p>No results found for this prompt.</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
    
  );
}

// Renderizar la aplicación
ReactDOM.render(<App />, document.getElementById('root'));

